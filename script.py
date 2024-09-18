import socket
import threading
import os
import time
from Functions import *
import re
from datetime import datetime
reps = 1
# Variáveis de ambiente
container_id = int(os.getenv('ID'))
cluster_port = int(os.getenv('CLUSTER_PORT'))

shared_file = '/shared/output.txt'
cabecalho = "cluster/id{"+str(container_id)+"}"
ok_message = cabecalho + "/OK"
containers = create_containers(5)
ok = 0
# Variável global de lock
request_lock = threading.Lock()

# Variáveis globais
message_to_write = ""  # Mensagem do cliente a ser escrita no arquivo
message_timestamp = float(9**10)
client_timestamp = -2
sair = False

def send_based_on_comparison(containers, client_timestamp, ok_message, comparison_type):
    for con in containers:
        if comparison_type == '<' and con['timestamp'] < client_timestamp:
            while send_message(con, ok_message) != "received":
                time.sleep(1)
        elif comparison_type == '>' and con['timestamp'] > client_timestamp:
            while send_message(con, ok_message) != "received":
                time.sleep(1)
        else:
            print(f"Tipo de comparação inválido: {comparison_type}. Use '<' ou '>'.")
            break

# Função do servidor para lidar com requisições de outros containers
def server():
    global containers
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen(1)
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            conn, _ = server_socket.accept()
            handle_request(conn)
            conn.close()

            

# Função que processa a requisição recebida do cluster
def handle_request(conn):
    global sair
    data = conn.recv(1024).decode()

    if not data:
        return

    if "/OK" in data or "RELEASE" in data or 'TIMESTAMP' in data:
        if 'TIMESTAMP' in data:
            conn.send(str(client_timestamp).encode())

        if "/OK" in data:
            c_id = extract_id(data)
            containers[c_id]['start'] = "OK"
            conn.send("received".encode())

        if "RELEASE" in data:
            sair = True
            conn.send("received".encode())
            #containers = create_containers(5)
    else:
        conn.send("message not processed".encode())


# Função para enviar mensagem a outro container e receber resposta
def send_message(container, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((f"container_{container['id'] + 1}", container['cluster_port']))
            sock.send(message.encode())
            return sock.recv(1024).decode()
    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {container['id']}")
        return -2


# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    global containers
    while True:
        for con in containers:
                con['timestamp'] = float(send_message(con, 'TIMESTAMP'))            
        if received_timestamps(containers):
            vote_and_write()
            break

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
        else:
            send_data(client_socket, "sleep")  # Informa que não pode processar a mensagem agora

def vote_and_write():
    global message_to_write, sair, containers
    containers[container_id]['start'] = "OK"
    #"cluster/id{3}"
    ok_message = cabecalho + "/OK"
    send_release = True
    
    if not containers:
        print(f"Container {container_id} não tem containers interessados para comparar.")
        return

    #Envia para os containers com timestamp menor que o meu
    for con in containers:
        if con['timestamp'] < client_timestamp:
            while send_message(con, ok_message) != "received":
                time.sleep(1)


    sorted_containers = sorted(containers, key=compare_by_timestamp)
    with open("/shared/debug.txt", 'a') as f:
        f.write(f"{container_id}------------ {client_timestamp} -------------------\n")
        for c in sorted_containers:
            f.write(f"{c}\n")

    while True:
        if received_oks(containers):
            if message_to_write != "":
                with open(shared_file, 'a') as f:
                    f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()}\n")
                    f.write(f"Mensagem: {message_to_write}\n")  # Adiciona a mensagem recebida
                    break
            else:
                break
        else:
           time.sleep(1)

    for con in containers:
        if con['timestamp'] > client_timestamp:
            while True:
                if send_message(con, ok_message) == "received":
                    break

    sorted_containers = sorted(containers, key=compare_by_timestamp)
    with open("/shared/debug.txt", 'a') as f:
        f.write(f"{container_id} =============== {client_timestamp} =================\n")
        for c in sorted_containers:
            f.write(f"{c}\n")

    if send_release:
        #Enviar RELEASE para os containers 
        for con in containers:
            send_message(con, "RELEASE")
    else:
        while True:
            if sair:
                break

    message_to_write = ""  # Limpa a mensagem depois de escrever
    sair = False

print(cabecalho)
print("OK" in ok_message)
print(extract_id(ok_message))



#Cria servidor para escutar o cliente
server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))
client_socket = accept_client(server_socket)
# Iniciando thread para escutar o cliente
threading.Thread(target=listen_client, args=(client_socket,)).start()

# Inicia a thread de votacao
threading.Thread(target=initiate_vote, args=()).start()
# Inicia o servidor para escutar o cluster
server()