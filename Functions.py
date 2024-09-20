import time
import re
import socket
import threading
import random
import os
file_path = "/shared/output.txt"


def create_containers(elements):
    return [{'id': i, 'cluster_port': 6000 + i, 'timestamp':-2, 'start': 'no', 'rele': 'no'} for i in range(elements)]

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
        return -2  # Retorna -1 para indicar falha na conexão
    except OSError as e:
        print(f"Erro ao enviar dados: {e}")    
    

# Função para extrair a mensagem
def extract_message(string):
    match = re.search(r"message\{(.+)\}", string)
    return match.group(1) if match else -1

def extract_id(string):
    # Ajusta a expressão regular para corresponder ao formato correto
    match = re.search(r"/id\{(\d+)\}", string)

    return int(match.group(1)) if match else -1

def extract_timestamp(string):
    match = re.search(r"timestamp\{([\d.]+)\}", string)
    return float(match.group(1)) if match else -1.0

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

def received_timestamps(containers):
    for con in containers:
        if con['timestamp'] == -2:
            return False
    return True 

def one_release(containers):
    for con in containers:
        if con['rele'] == "YES":
            return True
    return False 

def received_oks(containers):
    for con in containers:
        if con['start'] != 'OK':
            return False
    return True         
# Função de comparação de timestamps
def compare_by_timestamp(container):
    return container['timestamp']

def beautifull_print(containers):
    for con in containers:
        print(con)



#--------------------- TEST AREA
