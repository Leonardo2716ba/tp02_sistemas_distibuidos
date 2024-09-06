import time
import re
import socket
import os
file_path = "/shared/output.txt"

def receive_data(client):
    return client.recv(1024).decode('utf-8')

def send_data(client_socket, message):
    try:
        if not client_socket._closed:
            client_socket.send(message.encode('utf-8'))
        else:
            print("Tentativa de enviar dados em um socket fechado.")
    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {client_socket['id']}")
        return "-1"  # Retorna -1 para indicar falha na conexão
    except OSError as e:
        print(f"Erro ao enviar dados: {e}")    
    
# Função para extrair o timestamp
def extract_time_stamp(string):
    match = re.search(r"time\{(\d+)\}", string)
    return int(match.group(1)) if match else None

# Função para extrair a mensagem
def extract_message(string):
    match = re.search(r"message\{(.+)\}", string)
    return match.group(1) if match else None

def get_current_timestamp():
    return int(time.time())

def extract_id(string):
    # Ajusta a expressão regular para corresponder ao formato correto
    match = re.search(r"client/id\{(\d+)\}", string)
    match = re.search(r"/id\{(\d+)\}", string)

    return int(match.group(1)) if match else None

def extract_time_stamp(string):
    # Ajusta a expressão regular para corresponder ao formato correto
    match = re.search(r"timestamp\{(\d+)\}", string)
    return int(match.group(1)) if match else None

def write_timestamp_and_id(message):
    container_id = int(os.getenv('PORT')) - 5000
    #timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = extract_time_stamp(message)
    client_id = extract_id(message)
    w_message = extract_message(message)
    print(f"ID: {container_id}, Client:{client_id}, Timestamp: {timestamp}, Message: {w_message}")
    with open(file_path, "a") as f:
        f.write(f"ID: {container_id}, Client:{client_id}, Timestamp: {timestamp}, Message: {w_message}\n")

def create_server(host,port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Servidor aguardando conexões na porta {port}...")
    return server_socket

def accept_client(server_socket):
    client_socket, addr = server_socket.accept()
    print(f"Conexão estabelecida com {addr}")
    return client_socket

