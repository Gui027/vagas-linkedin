# 1. ATUALIZAÇÃO FINAL: Usar Python 3.11 para compatibilidade total com seu pip
FROM python:3.11-slim

# 2. Instalar dependências do sistema e GNUPG
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 3. Configurar chave do Google Chrome (Método Seguro Atualizado)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# 4. Instalar Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 5. Configurar pasta
WORKDIR /app

# 6. Instalar requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copiar código
COPY . .

# 8. Rodar
CMD uvicorn server:app --host 0.0.0.0 --port $PORT