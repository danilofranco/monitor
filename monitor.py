import psutil
import schedule
import time
import logging
import logging.handlers
import requests
import json
import smtplib
import subprocess
import docker
import os
from datetime import datetime, timedelta

# Carregar configurações
with open('config.json') as config_file:
    config = json.load(config_file)

# Configurar logging
logging.basicConfig(filename='system_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Conectar ao Docker Daemon
client = docker.from_env()

# Configurar logging
log_directory = "./logs"
os.makedirs(log_directory, exist_ok=True)
current_date = datetime.now().strftime("%Y-%m-%d")  # Obter a data atual como uma string formatada
log_file = os.path.join(log_directory, f"system_monitor_{current_date}.log")  # Inserir a data no nome do arquivo
handler = logging.handlers.TimedRotatingFileHandler(filename=log_file, when="midnight", backupCount=config['log_retention_days'])
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def clean_old_logs():
    retention_period = timedelta(days=config['log_retention_days'])
    for file_name in os.listdir(log_directory):
        file_path = os.path.join(log_directory, file_name)
        if os.path.getctime(file_path) < (datetime.now() - retention_period).timestamp():
            os.remove(file_path)
            logger.info(f"Arquivo de log antigo removido: {file_path}")

# Funções de notificação
def notify(message, subject=None):
    if config['notifications']['slack']:
        notify_slack(message)
    if config['notifications']['email'] and subject:
        notify_email(subject, message)
    if config['notifications']['log']:
        logger.info(message)

# Função para enviar notificações via Slack
def notify_slack(message):
    try:
        webhook_url = config['slack_webhook_url']
        payload = {'text': message}
        requests.post(webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Erro ao enviar notificação via Slack: {e}")

# Função para enviar notificações via e-mail
def notify_email(subject, body):
    try:
        sender_email = config['email']['sender']
        receiver_email = config['email']['receiver']
        password = config['email']['password']
        smtp_server = config['email']['smtp_server']
        port = config['email']['smtp_port']
        
        message = f"Subject: {subject}\n\n{body}"
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")

# Função para verificar o estado dos serviços
def check_services():
    services = config['services']
    for service in services:
        try:
            subprocess.check_call(["systemctl", "is-active", "--quiet", service])
            message = f"O serviço {service} está ativo."
            notify(message)
        except subprocess.CalledProcessError:
            message = f"ALERTA: O serviço {service} não está ativo!"
            notify(message, f"Alerta de Serviço: {service}")

# Funções para verificar o uso do sistema
def check_cpu_usage():
    threshold = config['thresholds']['cpu']
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > threshold:
        message = f"Uso elevado de CPU detectado: {cpu_usage}%"
        notify(message, "Alerta de CPU")

def check_memory_usage():
    threshold = config['thresholds']['memory']
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > threshold:
        message = f"Uso elevado de memória detectado: {memory_usage}%"
        notify(message, "Alerta de Memória")

def check_disk_space():
    threshold = config['thresholds']['disk']
    disk_usage = psutil.disk_usage('/').percent
    if disk_usage > threshold:
        message = f"Espaço em disco baixo detectado: {disk_usage}%"
        notify(message, "Alerta de Disco")

def check_network_traffic():
    threshold = config['thresholds']['network']
    network_traffic = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
    if network_traffic > threshold:
        message = f"Tráfego de rede elevado detectado: {network_traffic / (1024 * 1024):.2f} MB"
        notify(message, "Alerta de Rede")

# Função para verificar o estado dos containers do Docker
def check_docker_containers():
    try:
        containers_to_check = config['docker_containers']
        for container_name in containers_to_check:
            container = client.containers.get(container_name)
            if container.status != 'running':
                message = f"ALERTA: O container do Docker {container.name} ({container.id[:12]}) não está em execução!"
                notify(message, f"Alerta de Container do Docker: {container.name}")
            else:
                message = f"O container do Docker {container.name} está em execução."
                logger.info(message)
    except Exception as e:
        message = f"Erro ao verificar os containers do Docker: {e}"
        notify(message)

# Função para executar verificações de saúde
def run_health_checks():
    try:
        clean_old_logs()
        notify("Executando verificações do sistema...")
        check_cpu_usage()
        check_memory_usage()
        check_disk_space()
        check_network_traffic()
        check_services()
        check_docker_containers()
        notify("Verificações concluídas.")
    except Exception as e:
        notify(f"Erro durante as verificações: {e}")

# Agendar verificações de saúde para serem executadas a cada minuto
schedule.every(5).minutes.do(run_health_checks)

# Loop principal para executar tarefas agendadas
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        notify("Monitoramento interrompido pelo usuário.")
        break
    except Exception as e:
        notify(f"Erro inesperado: {e}")

