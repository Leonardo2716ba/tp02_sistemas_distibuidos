import socket
import threading
import os
import time

from Functions import (create_containers, extract_id, extract_id, extract_message,
                       extract_timestamp, send_data, create_server, accept_client)

# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))
backup = f"/shared/store/backup_{container_id}.txt"

containers = [{'id': i, 'cluster_port': 7100 + i} for i in range(3)]

# Variáveis globais
message_to_write = ""  # Mensagem do cliente a ser escrita no arquivo
client_timestamp = -2
sair = False

# Função do servidor para lidar com requisições de outros containers
def cluster_store_internal_server():
    global containers
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen(1)

        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            conn, _ = server_socket.accept()
            cluster_store_handle_request(conn)
            conn.close()

# Função que processa a requisição recebida do cluster
def cluster_store_handle_request(conn):
    data = conn.recv(1024).decode()
    if not data:
        return
    if "cluster_store" in data:
        with open(backup, 'a') as f:
            f.write(f"Escrevi mensagem do store_{extract_id(data)}\n")  
            conn.send("received".encode())
    else:
        conn.send("message not processed".encode())


# Função para enviar mensagem a outro container e receber resposta
def send_message(container, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            #sock.connect((f"0.0.0.0", container['cluster_port']))
            sock.connect((f"cluster_store_{container['id'] + 1}", container['cluster_port']))
            sock.send(message.encode())
            return sock.recv(1024).decode()
    except ConnectionRefusedError:
        return -2



# Função para ouvir as mensagens dos clientes e processar
def listen_cluster_sync_client(client_socket):

    while True:
        message = client_socket.recv(1024).decode('utf-8')

        if not message:
            print("Conexão fechada pelo cliente.")
            break

        # Extrai a mensagem e o timestamp da string recebida
        if message != "" and message_to_write == "":
            message_to_write = extract_message(message)
            client_timestamp = extract_timestamp(message)
            send_data(client_socket, "committed")  # Confirma que a mensagem foi armazenada
        else:
            send_data(client_socket, "sleep")  # Informa que não pode processar a mensagem agora


#Cria servidor para escutar o cliente
#server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))
#client_socket = accept_client(server_socket)

# Iniciando thread para escutar o cluster sync
#threading.Thread(target=listen_cluster_sync_client, args=(client_socket,)).start()

# Inicia o servidor para escutar o cluster store
#cluster_store_internal_server()

#with open("/shared/debug.txt", 'w') as f:
#    f.write(f"")  

with open(backup, 'w') as f:
    f.write(f"")  

threading.Thread(target=cluster_store_internal_server, args=()).start()

while True:
    for c in containers:
        msg = send_message(c, "cluster_store/id{"+ f"{container_id}" +"}")
        if container_id == 1:
            print(msg)
        time.sleep(3)
