# Sistema de Monitoramento

Este projeto é um script Python para monitorar os recursos do sistema, incluindo CPU, memória, disco, tráfego de rede, status dos serviços do sistema e status dos containers Docker. Ele pode enviar notificações via Slack, e-mail ou armazenar as informações em um arquivo de log.

Utilizei este [artigo como referência](https://www.makeuseof.com/python-system-monitoring-automate-how/)

## Requisitos

- Python 3.6 ou superior
- Docker (se você quiser monitorar os containers Docker)
- Bibliotecas Python listadas no arquivo `requirements.txt`

## Instalação

1. Clone o repositório:
    ```sh
    git clone https://github.com/danilofranco/monitor.git
    cd monitor
    ```

2. (Opcional) Crie um ambiente virtual:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # No Windows use `venv\Scripts\activate`
    ```

3. Instale as dependências:
    ```sh
    pip install -r requirements.txt
    ```

4. Copie o arquivo `config.json.example` para `config.json` e edite as configurações conforme necessário.

## Configuração

Edite o arquivo `config.json` para configurar os limites de alerta, canais de notificação e outros parâmetros. Aqui está um exemplo de configuração:

```json
{
    "thresholds": {
        "cpu": 50,
        "memory": 80,
        "disk": 75,
        "network": 104857600
    },
    "slack_webhook_url": "YOUR_SLACK_WEBHOOK_URL",
    "email": {
        "sender": "your-email@gmail.com",
        "receiver": "receiver-email@gmail.com",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-password"
    },
    "services": [
        {
            "name": "docker",
            "auto_restart": true
        },
        {
            "name": "smbd",
            "auto_restart": true
        }
    ],
    "docker_containers": ["meu_container1", "meu_container2"],
    "log_retention_days": 30,
    "notifications": {
        "slack": true,
        "email": true,
        "log": true
    }
}
```

## Execução

```sh
$ python monitor.py
```