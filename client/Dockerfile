# Usar uma imagem base do Python
FROM python:3.9-slim

# Copiar o script para o container
COPY client/Functions.py /app/Functions.py
COPY client/client.py /app/client.py

# Definir o diretório de trabalho
WORKDIR /app

# Comando para executar o script
CMD ["python", "client.py"]
