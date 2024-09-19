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

client_message = "" #receber a mensagem do cliente
client_timestamp = -2

containers = create_containers(5)

ok_escrita = 0
ok_ts = 0

#comunicação entre servidores
def server():
    global containers

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        #Socket para escutar servidor x servidor.
        server_socket.bind(('0.0.0.0', cluster_port))
        server_socket.listen(1)
        print(f"Container {container_id} ouvindo na porta {cluster_port}...")

        #Loop para o tempo inteiro estar lidando com interações entre servidores.
        while True:
            server_atual, _ = server_socket.accept()
            handle_request(server_atual)

            #enviar os TS para todos os servidores.
            envia_timestamps()
            print(f'timestamps enviados')


            #Verificar se todos os containers receberam todos os timestamps
            verifica_timestamps()
            print(f'timestamps verificados')

            #Ordena os TS e guarda apenas os que querem escrever.
            containers_interessados = ordena_timestamps()
            print(f'timestamps ordenados')

            #Manda OK_Escrita
            envia_permissao_escrita(containers_interessados)
            print(f'OK_ESCRITA enviados\n')

            #Aquele que recebe todos os OK, escreve no arquivo. Só escreve quando estiver os OK necessarios (sem race condition)
            if ok_escrita == (len(containers_interessados) - 1) : escreve_arquivo() 
            print(f'escreveu')

            #reseta tudo
            reseta()

            server_atual.close()

def reseta():
    global client_timestamp, client_message

    client_message = ""
    client_timestamp = -2

def escreve_arquivo():
    with open(shared_file, 'a') as f:
        f.write(f"Container {container_id} escreveu no arquivo em {datetime.now()}\n")
        f.write(f"Mensagem: {client_message}\n")  # Adiciona a mensagem recebida

def envia_permissao_escrita(containers_interessados):
    for con in containers_interessados:
        if client_timestamp > con['timestamp']:
            #manda um OK_ESCRITA pra todos os cont que tem TS maior que o meu
            send_message(con, 'OK_ESCRITA')


def ordena_timestamps():
    global containers

    sorted_containers = sorted([c for c in containers if c['timestamp'] >= 0], key=lambda x: x['timestamp'])
    return sorted_containers

def envia_timestamps():
    global ok_ts

    for con in containers:
        #manda timestamp pra todos os cont
        con['timestamp'] = float(send_message(con, 'TIMESTAMP')) 

        #Se ele receber um TS, acrescenta a variável de OK_TS, de forma a ter ok_ts = 5 apenas se receber todos.
        if con['timestamp'] != -2:
            ok_ts += 1

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

def verifica_timestamps():
    #verifica todos os containers interessados, ou seja, aqueles cujo timestamp é diferente de -2.
    if ok_ts == 5 : return True


def handle_request(server_atual):
    global ok_escrita

    #recebeu informação de algum servidor
    data = server_atual.recv(1024).decode()

    if not data:
        return

    #O servidor quer enviar um TIMESTAMP e todos os outros precisam receber.
    if "TIMESTAMP" in data:
        server_atual.send(str(client_timestamp).encode())

    #enviar OK quando um já estiver escrito.
    #logica: sempre que um servidor enviar um OK, o contador é incrementado.
    if "OK_ESCRITA" in data:
        ok_escrita += 1

# Função para ouvir as mensagens dos clientes e processar.
def listen_client(client_socket):
    global client_message, client_timestamp

    while True:
        message = client_socket.recv(1024).decode('utf-8') #mensagem inteira (junto com ID, PORT, etc)

        if not message:
            print("conexão fechada pelo cliente.")
            break

        #receber a mensagem caso exista
        if message != "" and client_message == "": 
            client_message = extract_message(message)
            client_timestamp = extract_timestamp(message)
            #conseguimos extrair informação do cliente (a mensagem e o seu timestamp)

            send_data(client_socket, "commited") 
        else:
            send_data(client_socket, "sleep") 




#Conectar o cliente no servidor
#Inicializar um servidor
server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))  #(host, port)
#Cliente em contato com o servidor
client_socket = accept_client(server_socket)

#thread para escutar o cliente
threading.Thread(target=listen_client, args=(client_socket,)).start()
print(f'Thread listen client rodando')

#thread para se comunicar com os outros servidores
threading.Thread(target=server, daemon=True).start()
print(f'Thread server rodando')

#thread para iniciar
