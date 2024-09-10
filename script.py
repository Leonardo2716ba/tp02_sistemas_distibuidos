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
message_to_write = ""  # Mensagem do cliente a ser escrita no arquivo
message_timestamp = float(9**10)
client_timestamp = float(9**10)


# Função do servidor para lidar com requisições de outros containers
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen()
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            cluster_element, _ = server_socket.accept()
            threading.Thread(target=handle_request, args=(cluster_element,)).start()

# Função que processa a requisição recebida
def handle_request(cluster_element):
    data = cluster_element.recv(1024).decode()
    if data == 'REQUEST':
        if  message_to_write != "":
            cluster_element.send(str(client_timestamp).encode())
        else:
            cluster_element.send("-1".encode())
        # Responde com o timestamp da última mensagem
    cluster_element.close()

# Função para enviar mensagem a outro container e receber resposta
def receive_time_stamp(container):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            
            sock.connect((f"container_{container['id'] + 1}", container['cluster_port']))
            sock.send('REQUEST'.encode())

            return sock.recv(1024).decode()
        
    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {container['id']}")
        return None

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[1]

def vote_and_write():
    global message_to_write, message_timestamp, client_timestamp

    # Obtém os timestamps de todos os containers interessados
    interested_containers = [
        (container, float(receive_time_stamp(container)))
        for container in containers if container['id'] != container_id
    ]
    
    # Inclui o timestamp do container atual e remove aqueles cujo timestamp é -1 
    interested_containers = [(container_id, client_timestamp)] + [c for c in interested_containers if c[1] is (not None) or (c[1] != "-1")]

    if not interested_containers:
        print(f"Container {container_id} não tem containers interessados para comparar.")
        return
    
    # Verifica se este container tem o menor timestamp
    min_container = min(interested_containers, key=compare_by_timestamp)

    if min_container[0] == container_id:
        print(f"Container {container_id} venceu a votação e está escrevendo no arquivo.")
        with open(shared_file, 'a') as f:
            f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()} - {min_container[1]}\n")
            f.write(f"Mensagem: {message_to_write}\n")  # Adiciona a mensagem recebida
        
        message_to_write = ""  # Limpa a mensagem depois de escrever
    else:
        print(f"Container {container_id} perdeu a votação.")

# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    while True:
        if message_to_write == "":
            time.sleep(5)
        else:
            vote_and_write()
            print(f"Container {container_id} está iniciando uma votação para escrever.")

# Função para ouvir as mensagens dos clientes e processar
def listen_client(client_socket):
    global message_to_write, client_timestamp

    while True:
        message = client_socket.recv(1024).decode('utf-8')

        if not message:
            print("Conexão fechada pelo cliente.")
            break

        # Extrai a mensagem e o timestamp da string recebida
        if message != "" and message_to_write == "":
            message_to_write = extract_message(message)
            client_timestamp = extract_time_stamp(message)
            send_data(client_socket, "committed")  # Confirma que a mensagem foi armazenada
        else:
            send_data(client_socket, "sleep")  # Informa que não pode processar a mensagem agora


# Inicia o servidor para escutar o cluster
threading.Thread(target=server, daemon=True).start()
# Inicia a thread de votacao
threading.Thread(target=initiate_vote, daemon=True).start()

#Cria servidor para escutar o cliente
server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))
client_socket = accept_client(server_socket)
# Iniciando thread para escutar o cliente
threading.Thread(target=listen_client, args=(client_socket,)).start()