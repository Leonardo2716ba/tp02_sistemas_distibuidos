import threading
import socket
import time
import random
from Functions import *
from datetime import datetime

def client_code(host, port):
    port = port + 5000
    commited = False
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))  # Conectar ao servidor
    timestamp = 999999999
    client_id = port - 5000
    lim = 10
    try:
        i = 0
        while True:
            if not commited:
                timestamp = datetime.now().timestamp()
                commited = True

            message = "client "+ str(client_id)+ " time: "+ str(timestamp) + " - message: "+ str(i)
            data = "client/id{"+ str(client_id) +"}/timestamp{"+ str(timestamp) + "}/message{"+ str(message) +"}"
            if i >= lim:
                data = ""
            if i == lim:
                print(f'Client {client_id} - Encerrou')
                i +=1
            client_socket.send(data.encode('utf-8'))
            cluster_command = receive_data(client_socket)
            print(cluster_command)
            if cluster_command == "sleep":   
                time.sleep(random.randint(1, 5))  # Pausa de 5 segundos para dar tempo ao servidor processar

            elif cluster_command == "committed":
                i+=1
                commited = False                


    except OSError as e:
        print(f"Erro ao enviar dados: {e}")
    except KeyboardInterrupt:
        client_socket.close()
    finally:
        client_socket.close()  # Fechar o socket do cliente


host = '0.0.0.0'
threading.Thread(target=client_code, args=(host,2)).start()
time.sleep(2)

threading.Thread(target=client_code, args=(host,3)).start()
time.sleep(2)
threading.Thread(target=client_code, args=(host,4)).start()
time.sleep(2)
threading.Thread(target=client_code, args=(host,0)).start()
time.sleep(2)
threading.Thread(target=client_code, args=(host,1)).start()