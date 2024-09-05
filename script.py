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

global my_message
my_message = ""

global n_elements
n_elements = 5

global cluster_messages
cluster_messages = ["","","","",""]
for i in cluster_messages:
    i = "/id{99}/timestamp{99999999}"

def less_timestamp():
    menor = -1
    for elemento in cluster_messages:  
        if extract_time_stamp(elemento) < menor:
            menor = extract_time_stamp(elemento)
    return menor

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
                write_message = client_new_message
                send_data(client_socket,"commited")
            else:
                send_data(client_socket, "sleep")


def client_server():
    global client_new_message
    global write_message
    global cluster_messages

    write_message = ""
    server_socket = create_server('0.0.0.0', int(os.getenv('PORT')))
    client_socket = accept_client(server_socket)

    my_port = int(os.getenv('PORT')+1000)

    client_server_thread = threading.Thread(target=listen_client,args=(client_socket,))
    client_server_thread.start()

    try:
        while True:
            if write_message != "":

                my_id = int(os.getenv('ID'))
                my_timestamp = extract_time_stamp(write_message)
                my_message = "cluster/id{" + str(my_id)+"}/timestamp{" + my_timestamp +"}"
                cluster_messages[my_id] = my_message

                broadcast_cluster(my_message, my_port);
                time.sleep(2)
                write_timestamp_and_id(write_message)

                if less_timestamp() == extract_time_stamp(my_message):
                    write_timestamp_and_id(write_message)

                    write_message = ""
                    my_message = "cluster/id{" + str(my_id)+"}/timestamp{999999999}"
                    broadcast_cluster(my_message, my_port);


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
    time.sleep(5)  # Espera o servidor iniciar


    while True:
        client_socket, addr = cluster_socket.accept()
        print(f"Connection from {addr}")
        message = client_socket.recv(1024).decode('utf-8')
        print(f"Received: {message}")
        
        if "cluster/" in message:
            i = extract_id(message)
            cluster_messages[i] = "cluster/id{"+i+"}/timestamp{"+extract_time_stamp(message)+"}"

        client_socket.close()

def broadcast_cluster(message, port):
    targets = [  # Corrigido o nome da variável
        ('element1', 6000),
        ('element2', 6001),
        ('element3', 6002),
        ('element4', 6003),
        ('element5', 6004)
    ]
    for element,target_port in targets:
        if target_port != port:  # Evita enviar para si mesmo
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            client_socket.connect(('localhost', target_port)) 
            client_socket.close()
            print(f"Message sent to {'localhost'}:{target_port}")


if __name__ == "__main__":

    #Escuta o cliente
    client_thread = threading.Thread(target=client_server).start()

    #Escuta o cluster
    cluster_thread = threading.Thread(target=cluster_server).start()
    #------------------------------------

    #------------------------------------
    client_thread.join()
    cluster_thread.join()