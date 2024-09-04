import socket

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(1)
    print("Servidor está aguardando conexão...")
    
    conn, addr = server_socket.accept()
    print(f"Conectado a {addr}")
    
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        print(f"Recebido: {data}")
        conn.sendall(data.encode())
    
    conn.close()

if __name__ == "__main__":
    start_server()
