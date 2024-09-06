import socket
import threading
import os
import time
from Functions import *
import re
from datetime import datetime

# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))
shared_file = '/shared/output.txt'
containers = [{'id': i, 'cluster_port': 6000 + i} for i in range(5)]  # Criação dinâmica da lista de containers

# Variáveis globais
client_message = ""  # Mensagem do cliente a ser escrita no arquivo
message_timestamp = float(9**10)


# Função do servidor para lidar com requisições de outros containers
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen()
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            conn, _ = server_socket.accept()
            threading.Thread(target=handle_request, args=(conn,)).start()

# Função que processa a requisição recebida
def handle_request(conn):
    global message_timestamp
    data = conn.recv(1024).decode()
    if data == 'REQUEST':
        # Responde com o timestamp da última mensagem
        conn.sendall(str(message_timestamp).encode())
    conn.close()

# Função para enviar mensagem a outro container e receber resposta
def send_message(container, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((f"container_{container['id'] + 1}", container['cluster_port']))
            sock.sendall(message.encode())
            return sock.recv(1024).decode()
    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {container['id']}")
        return None

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[1]

# Função de votação e escrita no arquivo
def vote_and_write():
    global client_message, message_timestamp

    if client_message == "":
        print(f"Container {container_id} não tem mensagem para escrever.")
        return

    # Obtém os timestamps de todos os containers interessados
    interested_containers = [
        (container, float(send_message(container, 'REQUEST')))
        for container in containers if container['id'] != container_id
    ]
    
    # Inclui o timestamp do container atual
    interested_containers = [(container_id, datetime.now().timestamp())] + [c for c in interested_containers if c[1] is not None]

    if not interested_containers:
        print(f"Container {container_id} não tem containers interessados para comparar.")
        return
    
    # Verifica se este container tem o menor timestamp
    min_container = min(interested_containers, key=compare_by_timestamp)
    if min_container[0] == container_id:
        print(f"Container {container_id} venceu a votação e está escrevendo no arquivo.")
        with open(shared_file, 'a') as f:
            f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()}\n")
            f.write(f"Mensagem: {client_message}\n")  # Adiciona a mensagem recebida
        
        client_message = ""  # Limpa a mensagem depois de escrever
    else:
        print(f"Container {container_id} perdeu a votação.")

# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    while True:
        time.sleep(5)
        print(f"Container {container_id} está iniciando uma votação para escrever.")
        vote_and_write()

# Função para ouvir as mensagens dos clientes e processar
def listen_client(client_socket):
    global client_message

    while True:
        message = client_socket.recv(1024).decode('utf-8')

        if not message:
            print("Conexão fechada pelo cliente.")
            break

        # Extrai a mensagem e o timestamp da string recebida
        msg = extract_message(message)
        if msg and client_message == "":
            client_message = msg
            message_timestamp = extract_time_stamp(message)
            send_data(client_socket, "committed")  # Confirma que a mensagem foi armazenada
        else:
            send_data(client_socket, "sleep")  # Informa que não pode processar a mensagem agora

# Inicia o servidor e o processo de votação
threading.Thread(target=server, daemon=True).start()
threading.Thread(target=initiate_vote, daemon=True).start()

# Define funções para criar e aceitar clientes (essas funções precisam ser definidas)
server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))
client_socket = accept_client(server_socket)
threading.Thread(target=listen_client, args=(client_socket,)).start()