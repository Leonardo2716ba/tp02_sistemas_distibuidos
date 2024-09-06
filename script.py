import socket
import threading
import os
import time
from Functions import *
from datetime import datetime

def listen_client(client_socket):
    global client_message  # Permite modificar a variável global client_message

    while True:
        # Recebe a mensagem do cliente
        message = client_socket.recv(1024).decode('utf-8')

        if not message:  # Se a mensagem estiver vazia, o cliente fechou a conexão
            print("Conexão fechada pelo cliente.")
            break

        # Se a mensagem contém "client/" e ainda não há mensagem armazenada
        if "client/" in message and client_message == "": 
            client_message = message
            send_data(client_socket, "committed")  # Confirma que a mensagem foi armazenada
        else:
            send_data(client_socket, "sleep")  # Informa que não pode processar a mensagem agora


# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))
shared_file = '/shared/output.txt'
containers = [{'id': i, 'cluster_port': 6000 + i} for i in range(5)]  # Criação dinâmica da lista de containers

def listen_client(client_socket):
    while True:
        message = ""
        message = client_socket.recv(1024).decode('utf-8')
        if not message:  # Se a mensagem estiver vazia, significa que o cliente fechou a conexão
            print("Conexão fechada pelo cliente.")
            break

        if "client/" in message and client_message == "": 
            client_message = message
            send_data(client_socket,"commited")
        else:
            send_data(client_socket, "sleep")

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
    global timestamp
    data = conn.recv(1024).decode()
    if data == 'REQUEST':
        timestamp = datetime.now().timestamp()  #Envia o timestamp atual caso queira escrever
        conn.sendall(str(timestamp).encode())  
    else:
        timestamp = -1; #Envia -1 caso não queira escrever
        conn.sendall(str(timestamp).encode()) 
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
    global timestamp
    timestamp = datetime.now().timestamp()  # Inicializa o timestamp para o container atual
    interested_containers = [
        (container, float(send_message(container, 'REQUEST')))
        for container in containers if container['id'] != container_id
    ]
    interested_containers = [(container_id, timestamp)] + [c for c in interested_containers if c[1]]

    # Inicializa o menor container e timestamp com os primeiros da lista
    min_container = interested_containers[0]

    # Itera por todos os containers interessados para encontrar o menor timestamp
    for container_data in interested_containers:
        # Verifica se o timestamp atual é menor que o menor timestamp já encontrado
        if container_data[1] < min_container[1] and container_data != -1:
            min_container = container_data  # Atualiza o menor container

    # Verifica se este container tem o menor timestamp
    if min_container[0] == container_id:
        print(f"Container {container_id} venceu a votação e está escrevendo no arquivo.")
        with open(shared_file, 'a') as f:
            f.write(f"Container {container_id}: {timestamp}\n")
    else:
        print(f"Container {container_id} perdeu a votação.")

# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    while True:
        time.sleep(5)
        print(f"Container {container_id} está iniciando uma votação para escrever.")
        vote_and_write()

# Inicia o servidor e o processo de votação
threading.Thread(target=server, daemon=True).start()
