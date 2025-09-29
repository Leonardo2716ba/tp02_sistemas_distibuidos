# Usar uma imagem base do Python
FROM python:3.9-slim

# Copiar o script para o container
COPY client/client_functions.py /app/client_functions.py
COPY client/client.py /app/client.py

# Definir o diretório de trabalho
WORKDIR /app

# Comando para executar o script
CMD ["python", "client.py"]
