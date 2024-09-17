import time
import re
import socket
import os
file_path = "/shared/output.txt"

import socket

def send_to_all_containers(containers, message):
    for container in containers:
        container_port = container['cluster_port']
        try:
            # Cria um socket TCP/IP
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Conecta no container na porta 'cluster_port'
                s.connect(('0.0.0.0', container_port))
                # Envia a mensagem
                s.send(message.encode('utf-8'))
                print(f"Mensagem enviada para o container {container['id']} na porta {container_port}")
        except ConnectionRefusedError:
            print(f"Refused {container['id']} na porta {container_port}")

def create_containers(elements):
    #        [0]            [1]                      [2]            [3]
    return [{'id': i, 'cluster_port': 6000 + i, 'timestamp':-2, 'start': "no"} for i in range(elements)]

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
    

# Função para extrair a mensagem
def extract_message(string):
    match = re.search(r"message\{(.+)\}", string)
    return match.group(1) if match else -1

def extract_id(string):
    # Ajusta a expressão regular para corresponder ao formato correto
    match = re.search(r"id\{(\d+)\}", string)

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

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[1]

def all_ok(containers):
    i = 0
    for con in containers:
        if con['start'] == "OK":
            i += 1
    return i == (len(containers) - 1)

def received_timestamps(containers):
    i = 0
    for con in containers:
        if con['timestamp'] != -2:
            i += 1
    return i == len(containers)

#print(create_containers())
#print(extract_timestamp("timestamp{13212}"))
#print(extract_id("id{13212}"))

#containers = create_containers(5)

#for con in containers:
#    con['timestamp'] = 3

#containers[2]['timestamp'] = -2
#print(received_timestamps(containers))