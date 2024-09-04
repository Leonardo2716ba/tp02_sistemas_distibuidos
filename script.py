from collections import namedtuple
import time
import os
from Functions import *
import threading
import socket
import datetime
file_path = "/shared/output.txt"

# Definir o caminho do arquivo compartilhado
global client_new_message
client_new_message = ""

global write_message
write_message = ""

global n_elements
n_elements = 5

global cluster_messages
cluster_messages = [0,0,0,0,0]
for i in cluster_messages:
    i = 999999999


def listen_client(client_socket):
    global client_new_message
    global write_message

    while True:
        client_new_message = ""
        client_new_message = client_socket.recv(1024).decode('utf-8')
        if not client_new_message:  # Se a mensagem estiver vazia, significa que o cliente fechou a conexão
            print("Conexão fechada pelo cliente.")
            break

        if "client/" in client_new_message: 
            if write_message == "":
                #realizar comparação entre os timestamps
                write_message = client_new_message
                send_data(client_socket,"commited")
            else:
                send_data(client_socket, "sleep")
            #realizar controle de timestamps repetidos


def client_server():
    global client_new_message
    global write_message
    write_message = ""
    server_socket = create_server('0.0.0.0',int(os.getenv('PORT')))
    client_socket = accept_client(server_socket)

    client_server_thread = threading.Thread(target=listen_client,args=(client_socket,))
    client_server_thread.start()

    try:
        while True:
            if write_message != "":
                write_timestamp_and_id(write_message)
                write_message = ""
                time.sleep(5)

    except OSError as e:
        print(f"Erro ao receber dados: {e}")
    except KeyboardInterrupt:
        client_socket.close()
        server_socket.close()
    finally:
        client_socket.close()
        server_socket.close()
        client_server_thread.join()


def cluster_server():
    cluster_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = int(os.getenv('PORT')) + 1000
    cluster_socket.bind(('0.0.0.0', port))
    cluster_socket.listen(5)
    print(f"Server running on port {port}")

    while True:
        client_socket, addr = cluster_socket.accept()
        print(f"Connection from {addr}")
        message = client_socket.recv(1024).decode('utf-8')
        print(f"Received: {message}")
        
        if "cluster/" in message:
            i = extract_id(message)
            cluster_messages[i] = extract_time_stamp(message)

        client_socket.close()

def send_message(target_host, target_port, message):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((target_host, target_port))
    client_socket.send(message.encode('utf-8'))
    client_socket.close()


if __name__ == "__main__":
    targets = [
        ('element1', 6000),
        ('element2', 6001),
        ('element3', 6002),
        ('element4', 6003),
        ('element5', 6004)
    ]    
    #Escuta o cliente
    client_thread = threading.Thread(target=client_server).start()

    #Escuta o cluster
    cluster_thread = threading.Thread(target=cluster_server).start()
    time.sleep(5)  # Espera o servidor iniciar
    #------------------------------------

    message = os.getenv('MESSAGE', f"Hello from element running on port {port}")

    for target_host, target_port in targets:
        if target_port != port:  # Evita enviar para si mesmo
            send_message(target_host, target_port, message)
            print(f"Message sent to {target_host}:{target_port}")

    #------------------------------------
    client_thread.join()
    client_thread.join()