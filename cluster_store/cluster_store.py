import socket
import threading
import os
import time
import random

from Functions import (extract_id, extract_message,
                       extract_timestamp, send_data, create_server, accept_client)

# Variáveis de ambiente
current_container_id = int(os.getenv('ID'))
backup_file_path = f"/shared/store/backup_{current_container_id}.txt"

failure_lim = 30
n_messages = 0
if current_container_id == 0:
    failure_lim = 18
elif current_container_id == 1:
    failure_lim = 10

message_to_write = ""
cluster_store = [{'id': i, 'cluster_port': 7100 + i} for i in range(3)]

test_sync = [{'id': i, 'cluster_port': 7001 + i} for i in range(1)]
# Variáveis globais
client_message_buffer = ""  # Mensagem do cliente a ser escrita no arquivo

# Função do servidor para lidar com requisições de outros containers
def listen_store(host, port):
    global containers
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Container {current_container_id} ouvindo na porta {port}...")
        while True:
            conn, _ = server_socket.accept()
            process_cluster_request(conn)
            conn.close()

# Função que processa a requisição recebida do cluster
def process_cluster_request(conn):
    global message_to_write, n_messages, failure_lim
    data = conn.recv(1024).decode()
    if not data:
        return
    
    if current_container_id == 0 or current_container_id == 1:
        if n_messages > failure_lim:
            conn.send("refused".encode())
            return
        
    if "cluster_store" in data:
        with open(backup_file_path, 'a') as f:
            f.write(f"{data}\n")  
        conn.send("received".encode())
        message_to_write = ""
    else:
        conn.send("refused".encode())

# Função para enviar mensagem a outro container e receber resposta
def send_cluster_message(container, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((f"cluster_store_{container['id'] + 1}", container['cluster_port']))
            sock.send(message.encode())
            return sock.recv(1024).decode()
    except ConnectionRefusedError:
        return -2

# Função do servidor para lidar com requisições de sincronização de containers
def listen_sync(host, port):
    global containers
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Container {current_container_id} ouvindo na porta {port}...")
        while True:
            conn, _ = server_socket.accept()
            process_sync_request(conn)
            conn.close()

# Função que processa a requisição de sincronização do cluster
def process_sync_request(conn):
    global message_to_write, failure_lim, n_messages
    data = conn.recv(1024).decode()
    if not data:
        return
    
    if current_container_id == 0 or current_container_id == 1:
        if n_messages > failure_lim:
            conn.send("refused".encode())
            return
        
    if "cluster_sync" in data and message_to_write == "":
        message_to_write = f"cluster_store_{current_container_id}/" + data[13:]
        broadcast_message_to_cluster(cluster_store, message_to_write)
        conn.send("received".encode())
        if current_container_id == 0 or current_container_id == 1:
            n_messages += 1
        while message_to_write != "":
            time.sleep(1)
    else:
        conn.send("message not processed".encode())

# Função para difundir (broadcast) a mensagem para o cluster
def broadcast_message_to_cluster(cluster_store, message):
    for c in cluster_store:
        while True:
            response = send_cluster_message(c, message)
            if response == "received":
                break
            elif response == "refused":
                print("ok")
                break
            #time.sleep(1)

# Criação de arquivo de backup
with open(backup_file_path, 'w') as f:
    f.write(f"")  

# Inicializando servidores
host = '0.0.0.0'
listen_cluster = int(os.getenv('CLUSTER_PORT'))
sync_port = int(os.getenv('PORT'))

threading.Thread(target=listen_store, args=(host, listen_cluster)).start()
threading.Thread(target=listen_sync, args=(host, sync_port)).start()