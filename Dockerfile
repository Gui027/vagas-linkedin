# 1. Usar uma imagem Python oficial
FROM python:3.9

# 2. Instalar Chrome e dependências do sistema
RUN apt-get update && apt-get install -y wget gnupg2 unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# 3. Configurar pasta de trabalho
WORKDIR /app

# 4. Copiar arquivos de requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante do código
COPY . .

# 6. Comando para iniciar o servidor (mesmo comando que você usava)
# O Render exige que a gente escute na porta $PORT
CMD uvicorn server:app --host 0.0.0.0 --port $PORT