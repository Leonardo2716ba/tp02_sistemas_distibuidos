import socket
import time
import random
from Functions import *

def main():
    quer_escrever = 0
    host = '0.0.0.0'
    #host = '192.168.31.108'
    port = int(os.getenv('PORT'))
    client_id = int(os.getenv('ID'))

    commited = False
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))  # Conectar ao servidor
    try:
        i = 0
        while True:
            #Se quer_escrever = 0, o cliente nao quer escrever.
            quer_escrever = random.randint(0,5)

            if not commited and quer_escrever != 0:
                timestamp = get_current_timestamp()
                commited = True

            if quer_escrever == 0:
                timestamp = -1
                commited = True

            #message = CLIENT 1 TIME 15 - MESSAGE 1
            message = "client "+ str(client_id)+ " time: "+ str(timestamp) + " - message: "+ str(i)

            if i >= 50:
                message = ""

            client_socket.send(message.encode('utf-8'))
            cluster_command = receive_data(client_socket)

            print(cluster_command)
            if cluster_command == "sleep":   
                time.sleep(random.randint(1, 5)) 
                
            elif cluster_command == "committed":
                i+=1
                commited = False


    except OSError as e:
        print(f"Erro ao enviar dados: {e}")
    except KeyboardInterrupt:
        client_socket.close()
    finally:
        client_socket.close()  # Fechar o socket do cliente

if __name__ == "__main__":  
    main()
