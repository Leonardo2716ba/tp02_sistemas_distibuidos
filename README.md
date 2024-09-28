
---

# Sincronização com Containers Docker

Este projeto implementa um sistema distribuído para sincronização de escrita em um arquivo compartilhado entre vários containers Docker. Cada container atua como um cliente e servidor, participando de um processo de votação para decidir quem tem permissão para escrever no arquivo.

## Estrutura do Projeto

O projeto contém dois principais serviços:

1. **Cluster Sync**: Containers que se comunicam entre si para votar e decidir qual deles irá escrever no arquivo compartilhado.
2. **Client**: Clientes que enviam mensagens para os containers, onde as mensagens são sincronizadas e escritas no arquivo após o processo de votação.

Cada container possui um `ID` único, uma porta para comunicação com o cliente e outra porta para comunicação com os outros containers do cluster.

## Arquivo Docker Compose

O arquivo `docker-compose.yml` define os serviços de sincronização (`cluster_sync`) e clientes para comunicação. Cada container é configurado com variáveis de ambiente que indicam seu ID e as portas de comunicação.

### Serviços Principais:

- **cluster_sync_1, cluster_sync_2, ... , cluster_sync_5**: Cada container no cluster tem um ID único e escuta em portas específicas para coordenar a sincronização.
- **client_1, client_2, ... , client_5**: Clientes que se conectam aos containers de sincronização para enviar mensagens.

O sistema de sincronização escreve as mensagens recebidas no arquivo compartilhado `shared_data/output.txt`.

## Como Executar

1. Clone o repositório do projeto:

    ```bash
    git clone https://github.com/Leonardo2716ba/tp02_sistemas_distibuidos.git
    cd tp02_sistemas_distibuidos
    ```

2. Certifique-se de que o Docker e o Docker Compose estejam instalados.

3. Execute o comando para iniciar os containers e construir as imagens:

    ```bash
    sudo docker-compose up --build
    ```

    Isso irá iniciar todos os containers de sincronização e os clientes associados.

4. A cada interação, as mensagens serão escritas no arquivo `shared_data/output.txt`.

    Para verificar as mensagens escritas, consulte o arquivo de saída:

    ```bash
    cat shared_data/output.txt
    ```

## Arquivo Compartilhado

- **shared_data/output.txt**: Este é o arquivo onde as mensagens sincronizadas serão escritas após o processo de votação entre os containers.

## Exemplo de Saída

A saída esperada no arquivo `shared_data/output.txt` será similar a:

```
Container 2 
Mensagem: client 2 time: 368186 - message: 3
Container 4 
Mensagem: client 4 time: 526895 - message: 3
Container 1 
Mensagem: client 1 time: 638613 - message: 3
Container 3 
Mensagem: client 3 time: 673766 - message: 3
Container 0 
Mensagem: client 0 time: 689581 - message: 3
########################################################
```

## Detalhes Técnicos

- Cada container se comunica via sockets.
- A comunicação entre os containers é usada para coordenar um processo de votação, garantindo que apenas um container possa escrever no arquivo compartilhado em um dado momento.
- O cliente envia mensagens com timestamps que os containers utilizam para decidir quem escreverá no arquivo.

## Encerrando os Containers

Para parar e remover os containers, use o comando:

```bash
sudo docker-compose down
```

---
