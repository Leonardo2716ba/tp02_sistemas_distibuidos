# Usar uma imagem base do Python
FROM python:3.9-slim

# Copiar o script para o container
COPY cluster_sync/cluster_sync.py /app/cluster_sync.py
COPY Functions.py /app/Functions.py

# Definir o diretório de trabalho
WORKDIR /app

# Comando para executar o script
CMD ["python", "cluster_sync.py"]
