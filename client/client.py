import socket
import time
import random
from Functions import *

def main():
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
            if not commited:
                timestamp = get_current_timestamp()
                commited = True

            message = "client "+ str(client_id)+ " time: "+ str(timestamp) + " - message: "+ str(i)
            data = "client/id{"+ str(client_id) +"}/timestamp{"+ str(timestamp) + "}/message{"+ str(message) +"}"
            if i >= 50:
                data = ""
            client_socket.send(data.encode('utf-8'))
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
