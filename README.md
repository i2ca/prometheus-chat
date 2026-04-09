# Prometheus - LCAD Voice & Control Interface

Este repositório contém o código-fonte do **Prometheus**, uma interface conversacional inteligente desenvolvida para o laboratório LCAD, projetada para interagir com o robô **Unitree G1**.

O sistema utiliza uma arquitetura distribuída para garantir processamento de IA em tempo real sem sobrecarregar o hardware de controle do robô.

## Arquitetura do Sistema

O projeto é dividido em três camadas principais:
1. **Frontend (Browser):** Captura de áudio via Web Speech API e comunicação bidirecional via WebSockets.
2. **Local Backend:** Servidor FastAPI que gerencia o estado da máquina física, intercepta comandos de segurança (ex: protocolo de café), controla o hardware do Unitree G1 e sintetiza voz localmente usando o modelo **Kokoro TTS**.
3. **Remote Brain:** Servidor dedicado que hospeda o Large Language Model (Qwen2.5:7b via Ollama) para processamento semântico e geração das respostas da personalidade Prometheus.

## ⚙️ Pré-requisitos

Para rodar este projeto localmente (no computador Argos), você precisará de:
* Python 3.10.
* Acesso à rede da VPN/Laboratório (para alcançar o servidor Atena no IP `10.9.8.252`).
* Certificados SSL locais (necessários para habilitar o microfone no navegador).

## Instalação e Configuração

**1. Clone o repositório e acesse a pasta:**

    git clone https://github.com/i2ca/prometheus-chat.git
    cd prometheus-chat

**2. Crie um ambiente virtual e instale as dependências:**

    python3.10 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

**3. Gere os certificados SSL (Obrigatório para a Web Speech API):**
Para que o navegador permita o uso do microfone, o servidor deve rodar em HTTPS. Gere os certificados de desenvolvimento rodando:

    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

*(Preencha as informações solicitadas no terminal ou apenas aperte Enter para todas).*

## Como Executar

A inicialização do projeto ocorre em duas etapas para garantir que o "cérebro" da IA esteja pronto antes da "interface" e do robô.

### Passo 1: Inicializar a IA na Atena (Servidor Remoto)
Conecte-se ao servidor Atena e inicie o serviço do Ollama expondo a porta correta para a rede do laboratório:

    ssh hercules@10.9.8.252
    cd ~/DEV/voz-prometheus-lcad
    OLLAMA_HOST="0.0.0.0:11435" ./bin/ollama serve

*(Mantenha este terminal aberto ou rode em uma sessão de background como `tmux` ou `screen`).*

### Passo 2: Inicializar o Servidor Principal
Em um novo terminal no seu computador local, com o ambiente virtual ativado, inicie a aplicação principal:

    python main.py

*O Uvicorn iniciará o servidor web e de WebSockets.*

### Passo 3: Acessar a Interface
Abra o seu navegador (recomenda-se Google Chrome) e acesse:
`https://localhost:8000` ou `https://127.0.0.1:8000`
*(Nota de Desenvolvimento: O navegador avisará que o certificado SSL não é seguro por ser autoassinado. Clique em "Avançado" e depois em "Ir para localhost").*

## Comandos de Hardware Suportados

Atualmente, o Prometheus possui interceptação lógica rígida para o protocolo de preparo de café.
* **Comando de voz sugerido:** *"Prometheus, faz um café pra mim."*
* O sistema exigirá uma confirmação verbal (*"sim", "autorizado", "quero"*) antes de acionar a rotina física no módulo `robot_hardware.py`.

## Estrutura de Arquivos

* `main.py`: Servidor FastAPI, gerenciamento de WebSockets, roteamento LLM e lógica de interceptação de segurança.
* `robot_hardware.py`: Módulo de integração com a SDK do Unitree G1.
* `templates/index.html`: Interface visual do usuário.
* `static/`: Arquivos estáticos (CSS, imagens, favicon).
* `requirements.txt`: Dependências do projeto Python.