# 1. Usar uma imagem Python oficial (baseada em Debian)
FROM python:3.9-slim

# 2. Instalar dependências básicas e o GNUPG (essencial para evitar erro 127)
# O erro 127 acontecia porque o sistema tentava usar comandos de chave sem ter o gnupg instalado corretamente.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 3. Baixar a chave oficial do Google e configurar o repositório (Método Novo/Seguro)
# Em vez de 'apt-key add', usamos o 'gpg --dearmor' e salvamos em keyrings.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# 4. Instalar o Google Chrome Stable
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 5. Configurar pasta de trabalho
WORKDIR /app

# 6. Copiar arquivos de requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copiar o restante do código
COPY . .

# 8. Comando para iniciar o servidor
CMD uvicorn server:app --host 0.0.0.0 --port $PORT