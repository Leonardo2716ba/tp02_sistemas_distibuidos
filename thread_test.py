import threading
import socket
import time
import random
from Functions import *

def client_code(host, port):
    port = port + 5000
    commited = False
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))  # Conectar ao servidor
    timestamp = 999999999 #inicializa
    client_id = port - 5000
    try:
        i = 0
        while i <= 5:
            if not commited:
                timestamp = get_current_timestamp()
                commited = True

            message = "client "+ str(client_id)+ " time: "+ str(timestamp) + " - message: "+ str(i)
            data = "client/id{"+ str(client_id) +"}/timestamp{"+ str(timestamp) + "}/message{"+ str(message) +"}"
            if i > 5:
                data = ""
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
threading.Thread(target=client_code, args=(host,0)).start()
threading.Thread(target=client_code, args=(host,1)).start()
threading.Thread(target=client_code, args=(host,2)).start()
threading.Thread(target=client_code, args=(host,3)).start()
threading.Thread(target=client_code, args=(host,4)).start()