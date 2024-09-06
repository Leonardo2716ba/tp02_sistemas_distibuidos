import socket
import threading
import os
import time
from datetime import datetime

# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))
shared_file = '/shared/output.txt'
containers = [{'id': i, 'cluster_port': 6000 + i} for i in range(5)]  # Criação dinâmica da lista de containers

timestamp = datetime.now().timestamp()  # Timestamp gerado na inicialização

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
        timestamp = datetime.now().timestamp()  # Atualiza o timestamp
        conn.sendall(str(timestamp).encode())  # Responde com o timestamp
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
    interested_containers = [
        (container, float(send_message(container, 'REQUEST')))
        for container in containers if container['id'] != container_id
    ]
    interested_containers = [(container_id, timestamp)] + [c for c in interested_containers if c[1]]

    # Verifica se este container tem o menor timestamp
    if min(interested_containers, key=compare_by_timestamp)[0] == container_id:
        print(f"Container {container_id} venceu a votação e está escrevendo no arquivo.")
        with open(shared_file, 'a') as f:
            f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()}\n")
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
initiate_vote()