# Use Python 3.9 como imagem base
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo requirements.txt
COPY requirements.txt .

# Atualize o pip antes de instalar as dependências
RUN pip install --upgrade pip

# Instale as dependências listadas no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install numpy==1.26.4

ENV FLASK_ENV=production

# Copie o código da aplicação para o diretório de trabalho
COPY . .

# Exponha a porta que sua aplicação vai utilizar (caso necessário)
EXPOSE 8080

# Comando para rodar a aplicação
CMD ["python", "-u", "main.py"]
