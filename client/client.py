import socket
import time
from Functions import *

def main():
    host = '0.0.0.0'
    #host = '192.168.31.108'
    port = int(os.getenv('PORT'))
    commited = False
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))  # Conectar ao servidor
    timestamp = 999999999
    client_id = int(os.getenv('ID'))
    try:
        i = 0
        while i < 25:
            #message = input("Digitar mernsagem:")
            if not commited:
                timestamp = get_current_timestamp()
                commited = True

            message = "Message: "+ str(i)
            data = "client/id{"+ str(client_id) +"}/timestamp{"+ str(timestamp) + "}/message{"+ str(message) +"}"
            client_socket.send(data.encode('utf-8'))

            cluster_command = receive_data(client_socket)
            print(cluster_command)
            if cluster_command == "sleep":   
                time.sleep(5)  # Pausa de 5 segundos para dar tempo ao servidor processar

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
