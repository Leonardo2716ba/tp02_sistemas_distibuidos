import socket
import threading
import os
import time
from Functions import *
import re
from datetime import datetime

#um vetor de timestamps. Sempre que recebe uma nova mensagem, o TS é
#adicionado no vetor. O vetor é ordenado novamente, e se envia um 
#sinal para o menor escrever, e o menor envia um sinal para o prox
#escrever.

#Variáveis de ambiente
container_port = int(os.getenv('PORT'))
container_id = int(os.getenv('ID')) 
cluster_port = int(os.getenv('CLUSTER_PORT'))
shared_file = '/shared/output.txt'
containers = [{'id': i, 'cluster_port': 6000 + i} for i in range(5)]  # Criação dinâmica da lista de containers

# Dicionário para armazenar timestamps recebidos
received_timestamps = {container['id']: None for container in containers}

# Variáveis globais
message_to_write = ""  # Mensagem do cliente a ser escrita no arquivo
message_timestamp = float(9**10) #inicializando
client_timestamp = float(9**10) #inicializando
write_permission = False

#Conecta todos os servidores no cluster.
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen()
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")
        while True:
            cluster_element, _ = server_socket.accept()
            #Enquanto o servidor estiver conectado, ficará vendo se o servidor quer escrever
            #Ou seja, esperando que a segunda thread rode e ache um request.
            threading.Thread(target=handle_request, args=(cluster_element,)).start() 

#Verifica se o servidor quer escrever
def handle_request(cluster_element):
    global write_permission
    data = cluster_element.recv(1024).decode() #recebe mensagem do servidor (Request ou nada)
    #Servidor quer escrever (cliente pediu)
    if data.startswith('REQUEST'):
        #tem mensagem pra escrever (somente quando o servidor já tiver
        #recebido uma mensagem do cliente na função listen_client)
        if message_to_write != "":
            response = f"{client_timestamp},{container_id},{message_to_write}"
            cluster_element.send(response.encode())  # Envia o timestamp, ID do container e mensagem
        else:
            cluster_element.send("-1".encode())
        
    # Recebe os timestamps de outros containers
    elif data.startswith('TIMESTAMP'):
        _, timestamp, sender_id = data.split(',')
        received_timestamps[int(sender_id)] = float(timestamp)
        cluster_element.send("OK".encode())  # Envia um Ok de volta para confirmar o recebimento
    
    # Recebe o sinal de permissão para escrever
    elif data == "WRITE_NEXT":
        print(f"Container {container_id} recebeu permissão para escrever.")
        write_permission = True  # Seta a permissão para escrever

    cluster_element.close()


# Envia o timestamp para todos os containers do cluster
def send_timestamp_to_all():
    for container in containers:
        #Nao envia para ele mesmo
        if container['id'] != container_id:
            try:
                #cria um novo sock
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((f"container_{container['id'] + 1}", container['cluster_port']))
                    #recebe o timestamp de todos os servidores
                    message = f"TIMESTAMP,{client_timestamp},{container_id}"
                    #envia para o cluster
                    sock.send(message.encode())
                    #recebe o OK
                    response = sock.recv(1024).decode()
                    print(f"Recebido {response} de container {container['id']}")
            except ConnectionRefusedError:
                print(f"Falha ao conectar no container {container['id']}")

# Função que inicia o ciclo de votação periodicamente
def initiate_vote():
    while True:
        #Se a mensagem for string vazia, dormir.
        if message_to_write == "":
            time.sleep(5)

        else:
            ##duvida em tirar esse eLSE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            vote_and_write()
            print(f"Container {container_id} está iniciando uma votação para escrever.")

# Função para conenctar o container no cluster, enviar uma mensagem
# para o cluster saber que o container quer escrever.
def receive_time_stamp(container):
    try:
        #criou um novo socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            #conectou o container no cluster
            sock.connect((f"container_{container['id'] + 1}", container['cluster_port']))
            #enviou REQUEST para o cluster
            sock.send('REQUEST'.encode())

            #recebe o timestamp ou -1 se vazio
            return sock.recv(1024).decode()
        
    except ConnectionRefusedError:
        print(f"Falha ao conectar no container {container['id']}")
        return None

# Função para verificar se todos os servidores receberam todos os timestamps
def check_all_timestamps_received():
    while True:
        # Verifica se todos os servidores têm todos os timestamps
        # Função all retorna true se todos os elementos do iteravel forem verdadeiros
        if all(timestamp is not None for timestamp in received_timestamps.values()):
            print("Todos os servidores receberam todos os timestamps.")
            break
        else:
            print("Esperando todos os timestamps serem recebidos...")
            time.sleep(1)  # Espera um pouco antes de verificar novamente


#Função para votar e escrever
def vote_and_write():
    global message_to_write, message_timestamp, client_timestamp, write_permission
    send_timestamp_to_all()  # Envia o timestamp para todos os servidores antes de iniciar a votação

    # Obtém os timestamps de todos os containers interessados, criando
    # Uma tupla interested_containers = [container, timestamp]
    interested_containers = [
        #receive_time_stamp vai mandar o REQUEST e vai ser feito
        #a verificação se todos receberam o timestamp
        (container, float(receive_time_stamp(container))) 
        for container in containers 
    ]

    #tira os containers que não estão interessados em escrita (timestamp -1)
    interested_containers = [
        (container, timestamp) 
        for container, timestamp in interested_containers
        if timestamp != -1
    ]

    # Verificação se todos os servidores possuem todos os timestamps
    check_all_timestamps_received()

    #ordenando por TS
    interested_containers = sorted(interested_containers, key=lambda x: x[1])
   
    # Identifica o container com o menor timestamp
    min_container = min(interested_containers, key=lambda x: x[1])

    if (container_id == min_container[0]['id']): write_permission = True
    # Verifica se este container é o primeiro a escrever ou se recebeu permissão para escrever

    while (True): 
        if write_permission == True : break #vai esperar sua vez.

    if write_permission:
        print(f"Container {container_id} está escrevendo no arquivo.")
        with open(shared_file, 'a') as f:
            f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()} - {min_container[1]}\n")
            f.write(f"Mensagem: {message_to_write}\n")  # Adiciona a mensagem recebida
        
        message_to_write = ""  # Limpa a mensagem depois de escrever
        write_permission = False  # Reseta a permissão após escrever
        client_timestamp = -1

        #manda uma mensagem pro proximo container de menor timestamp além dele escrever no arquivo
        send_message_to_next(interested_containers, min_container)
    else:
        print(f"Container {container_id} perdeu a votação ou está aguardando permissão.")

def send_message_to_next(containers, min_container):
    # Ordena os containers por timestamp
    containers_sorted = sorted(containers, key=lambda x: x[1])
    
    # Encontra o índice do container atual
    current_index = containers_sorted.index(min_container)
    
    # Verifica se há um próximo container para enviar a mensagem
    if current_index + 1 < len(containers_sorted):
        next_container = containers_sorted[current_index + 1]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((f"container_{next_container[0]['id'] + 1}", next_container[0]['cluster_port']))
                # Envia uma mensagem para o próximo container, dando permissão para escrever
                sock.send("WRITE_NEXT".encode())
                print(f"Mensagem enviada para o próximo container {next_container[0]['id']} para escrever.")
        except ConnectionRefusedError:
            print(f"Falha ao conectar no próximo container {next_container[0]['id']}")
    else:
        print("Não há mais containers na fila para escrever.")

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[1]

#Ouvindo o cliente do servidor. Função recebe a mensagem, armazena e manda um sinal para
#O cliente saber se a mensagem dele foi armazenada ou não.
def listen_client(client_socket):
    global message_to_write, client_timestamp

    while True:
        #cliente está mandando uma mensagem
        message = client_socket.recv(1024).decode('utf-8')

        if not message:
            print("Conexão fechada pelo cliente.")
            break

        # Extrai a mensagem e o timestamp da string recebida
        if message != "" and message_to_write == "":
            message_to_write = extract_message(message)
            client_timestamp = extract_time_stamp(message)

            #mandando um comitted para o cliente ficar ciente.
            send_data(client_socket, "committed")
        else:
            #informa que não pode processar a mensagem agora
            message_to_write = ""
            client_timestamp = -1
            send_data(client_socket, "sleep") 


#Cria servidor para escutar o cliente. Todos as maquinas também serão servidor.
server_socket = create_server('0.0.0.0', container_port) #(host, port)
#Conecta o cliente no servidor específico de cada maquina.
client_socket = accept_client(server_socket)

# Inicia o servidor para escutar o cluster
threading.Thread(target=server, daemon=True).start()

# Iniciando thread para escutar o cliente
threading.Thread(target=listen_client, args=(client_socket,)).start()

# Inicia a thread de votacao
threading.Thread(target=initiate_vote, daemon=True).start()

#A thread server inicializa os servidores para se conectar com seu cliente
#A thread listen client recebe mensagem do cliente e envia para ele se foi recebida ou não
#Só quando a mensagem foi recebida, a thread iniate_vote consegue rodar propriamente