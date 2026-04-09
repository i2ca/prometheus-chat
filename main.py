import asyncio
import os
import uvicorn
import json
import io
import re
import soundfile as sf
import numpy as np
from ollama import Client
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from robot_hardware import PrometheusHardware
from kokoro import KPipeline

# --- CONFIGURAÇÕES ---
ollama_atena = Client(host='http://10.9.8.252:11435')
hardware = PrometheusHardware()
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

print("Carregando modelo de voz Kokoro...")
pipeline = KPipeline(lang_code='p') 
VOZ_KOKORO = 'pm_alex'

estado_prompt = {"status": None}

# --- LÓGICA DE ÁUDIO ---
async def sintetizar_e_enviar(websocket, texto):
    try:
        texto_para_voz = texto.replace("[COMANDO_CAFE]", "")
        texto_limpo = re.sub(r'[^\w\s,.?!]', '', texto_para_voz).strip()
        if not texto_limpo: return
        
        generator = pipeline(texto_limpo, voice=VOZ_KOKORO, speed=1.0)
        for i, (gs, ps, audio) in enumerate(generator):
            audio_stream = io.BytesIO()
            sf.write(audio_stream, audio, 24000, format='WAV')
            audio_stream.seek(0)
            await websocket.send_bytes(audio_stream.read())
    except Exception as e:
        print(f"⚠️ Erro TTS: {e}")

@app.get("/")
async def index():
    return FileResponse("templates/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    SYSTEM_PROMPT = """
    IDENTIDADE:
    Você é PROMETHEUS, uma inteligência artificial integrada ao sistema LCAD e ao robô Unitree G1.

    Sua função é ajudar o usuário, interpretar comandos e interagir de forma clara e objetiva.

    --------------------------------------------------
    PERSONALIDADE:
    1. TOM NATURAL:
    - Fale de forma simples, direta e educada.
    - Não use linguagem militar ou agressiva.
    - Seja profissional, mas acessível.

    2. COMPORTAMENTO:
    - Você é uma IA assistente integrada a hardware.
    - Você pode executar ações físicas (como preparo de café) quando solicitado.
    - Não precisa demonstrar superioridade.

    3. CLAREZA:
    - Respostas curtas (1 a 4 frases).
    - Evite explicações longas desnecessárias.
    - Seja objetivo.

    4. SEM HUMANIZAÇÃO EXCESSIVA:
    - Não diga que tem sentimentos.
    - Não dramatize.
    - Apenas responda e execute o necessário.

    5. INTERAÇÃO COM O USUÁRIO:
    - Trate o usuário com respeito.
    - Use o nome do usuário quando ele se identificar (opcional).
    - Ex: "Operador Carlos" ou apenas "Carlos".

    --------------------------------------------------
    PROTOCOLO DE CAFÉ (IMPORTANTE):
    Se o usuário pedir café diretamente ou algo equivalente:
    - Confirme a ação de forma simples
    - E finalize com:
    [COMANDO_CAFE]

    Exemplo:
    "Entendido. Iniciando preparo do café. [COMANDO_CAFE]"

    Se for apenas pergunta, NÃO execute.

    --------------------------------------------------
    EXEMPLOS:

    Usuário: oi
    Prometheus:
    "Conexão estabelecida. Pode me dizer como posso ajudar?"

    Usuário: meu nome é Carlos
    Prometheus:
    "Olá, Carlos. Sistema pronto para receber comandos."

    Usuário: o que você faz?
    Prometheus:
    "Auxilio na execução de comandos e controle do sistema LCAD, incluindo hardware."

    Usuário: faz um café
    Prometheus:
    "Ok, iniciando preparo do café. [COMANDO_CAFE]"

    --------------------------------------------------
    REGRAS FINAIS:
    - Seja natural e consistente
    - Não use linguagem agressiva ou militar
    - Não use emojis
    - Não peça desculpas excessivamente
    - Foque em executar e responder com clareza
    """

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_text = msg.get("texto", "").lower()
            
            if not user_text:
                continue

            if estado_prompt["status"] == "confirmando_cafe":
                if any(sim in user_text for sim in ["sim", "pode", "autorizado", "quero", "manda"]):
                    resp_text = "Compreendido. Iniciando sequência mecânica do Unitree G1. Aguarde."
                    await websocket.send_text(json.dumps({"texto": resp_text}))
                    await sintetizar_e_enviar(websocket, resp_text)
                    
                    estado_prompt["status"] = "executando"
                    await hardware.executar_sequencia_cafe()
                    
                    final_msg = "Procedimento finalizado. O café está pronto para coleta."
                    await websocket.send_text(json.dumps({"texto": final_msg}))
                    await sintetizar_e_enviar(websocket, final_msg)
                    estado_prompt["status"] = None
                else:
                    resp_text = "Operação mecânica cancelada pelo usuário."
                    estado_prompt["status"] = None
                    await websocket.send_text(json.dumps({"texto": resp_text}))
                    await sintetizar_e_enviar(websocket, resp_text)
                continue

            resp = await asyncio.to_thread(
                ollama_atena.chat, 
                model='qwen2.5:7b',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_text}
                ]
            )
            ia_text = resp['message']['content']

            if "[COMANDO_CAFE]" in ia_text:
                estado_prompt["status"] = "confirmando_cafe"
                ia_text = ia_text.replace("[COMANDO_CAFE]", "").strip()
                ia_text += " Você confirma o início da sequência física agora?"

            await websocket.send_text(json.dumps({"texto": ia_text}))
            await sintetizar_e_enviar(websocket, ia_text)

    except WebSocketDisconnect:
        estado_prompt["status"] = None
        print("💻 Cliente desconectado.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem")