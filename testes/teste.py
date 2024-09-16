from datetime import datetime

containers = [{'id': i, 'cluster_port': 6000 + i} for i in range(5)]  # Criação dinâmica da lista de containers
container_id = 0

# Função de comparação de timestamps
def compare_by_timestamp(container_data):
    return container_data[1]

def vote_and_write():
    global client_message, message_timestamp, client_timestamp
    
    # Inclui o timestamp do container atual e remove aqueles cujo timestamp é -1
    interested_containers = [(1,100),(0,100),(2,300),(3,400)]
    if not interested_containers:
        return
    
    # Verifica se este container tem o menor timestamp
    min_container = min(interested_containers, key=compare_by_timestamp)
    print(min_container)

    if min_container[0] == container_id:
        print(f"Container {container_id} venceu a votação e está escrevendo no arquivo.")
        
        client_message = ""  # Limpa a mensagem depois de escrever
    else:
        print(f"Container {container_id} perdeu a votação.")

vote_and_write()

# Obtendo o timestamp atual
i = 0
while True:
    timestamp = datetime.now().timestamp()
    i+=1
    print("",end="")
    timestamp2 = datetime.now().timestamp()
    if(timestamp2 == timestamp):
        print(timestamp2 == timestamp)
        print(f'{timestamp} == {timestamp2}');