import socket
import threading
import os
import time
from Functions import *

from datetime import datetime
n_elements=5
# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))
shared_file = '/shared/output.txt'
cabecalho = "cluster/id{"+ container_id +"}/"

containers = create_containers(n_elements)

# Variáveis globais
message_to_write = ""  # Mensagem do cliente a ser escrita no arquivo
message_timestamp = float(9**10)
client_timestamp = float(9**10)


# Função do servidor para lidar com requisições de outros containers
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen(n_elements)
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            cluster_element, _ = server_socket.accept()
            threading.Thread(target=handle_request, args=(cluster_element,)).start()

# Função que processa a requisição recebida
def handle_request(cluster_element):
    global containers
    data = cluster_element.recv(1024).decode()
    c_id = extract_id(data)

    if "OK" in data:
        containers[c_id]['start'] = 'OK'
    #cluster_element.send(str(client_timestamp).encode())
    elif containers[container_id]['timestamp'] == -2:
        containers[c_id]['timestamp'] = extract_timestamp(data)

    cluster_element.close()

# Função para enviar mensagem a outro container e receber resposta
def send_message(container, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((f"container_{container['id']}", container['cluster_port']))
            sock.send(message.encode())

    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {container['id']}")

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[2]

def vote_and_write():
    global message_to_write
    #"cluster/id{3}"
    ok_message = cabecalho + "/OK"
    send_release = True
    
    sorted_containers = sorted(containers, key=compare_by_timestamp)

    if not sorted_containers:
        print(f"Container {container_id} não tem containers interessados para comparar.")
        return
    
    #Envia para os containers com timestamp menor que o meu
    for con in sorted_containers:
        #message = "cluster/id{"+ container_id +"}/timestamp{"+ client_timestamp +"}"
        if con['timestamp'] < client_timestamp:
            send_message(con, ok_message)
    
    while True:
        if all_ok(containers):
            if message_to_write != "":
                with open(shared_file, 'a') as f:
                    f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()}\n")
                    f.write(f"Mensagem: {message_to_write}\n")  # Adiciona a mensagem recebida
                    break
            else:
                break
        else:
            time.sleep(1)

    #Envia para os containers com timestamp maior que o meu
    for con in sorted_containers:
        if con['timestamp'] > client_timestamp:
            send_message(con, ok_message)
            send_release = False
            

    if send_release:
        #Enviar RELEASE para os containers 
        for con in sorted_containers:
            send_message(con, "RELEASE")
    #esperar receber release
    message_to_write = ""  # Limpa a mensagem depois de escrever

# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    while True:
        if received_timestamps(containers):
            vote_and_write()
        else:
            time.sleep(1)

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
            client_timestamp = extract_timestamp(message)
            send_data(client_socket, "committed")  # Confirma que a mensagem foi armazenada
            for con in containers:
                send_message(con, "cluster/{"+ str(container_id) + "}/timestamp{"+ str(client_timestamp)) +"}"
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