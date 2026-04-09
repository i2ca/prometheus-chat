# robot_hardware.py
import asyncio

class PrometheusHardware:
    def __init__(self):
        # Aqui ficarão as configurações da SDK do Unitree (lerobot, etc) no futuro
        self.tarefas_cafe = [
            "Levantar a chaleira",
            "Levantar a xícara",
            "Retirar a tampa do açúcar e colocá-la na mesa",
            "Posicionar a xícara abaixo do filtro"
        ]

    async def executar_sequencia_cafe(self):
        """
        Executa a sequência de movimentos e trava a execução até terminar.
        """
        print("\n⚙️ [Hardware] INICIANDO PROTOCOLO DE CAFÉ...")
        
        for i, tarefa in enumerate(self.tarefas_cafe):
            print(f"⚙️ [Hardware] Executando Etapa {i+1}: {tarefa}")
            # Simula o tempo que o robô leva para fazer o movimento físico
            await asyncio.sleep(4.0) 
            
        print("⚙️ [Hardware] PROTOCOLO DE CAFÉ CONCLUÍDO.\n")
        return True