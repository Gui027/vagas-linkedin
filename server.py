# server.py
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import executar_raspagem, ARQUIVO_CSV
import csv
import os
import uvicorn

app = FastAPI(title="API Vagas LinkedIn - Agendada")

# --- CONFIGURAÇÃO DO AGENDADOR (10h e 18h) ---
scheduler = BackgroundScheduler()

# Job 1: 10:00 da manhã
scheduler.add_job(executar_raspagem, 'cron', hour=10, minute=0)

# Job 2: 18:00 da tarde
scheduler.add_job(executar_raspagem, 'cron', hour=14, minute=37)

# Job de Teste: Descomente abaixo se quiser ver rodando daqui a 1 minuto para testar
# scheduler.add_job(executar_raspagem, 'interval', minutes=1)

scheduler.start()

# --- ENDPOINTS ---
@app.get("/")
def status():
    return {
        "sistema": "Online",
        "agendamento": "Automático às 10:00 e 18:00",
        "prox_execucao": str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else "N/A"
    }

@app.get("/vagas")
def pegar_dados():
    dados = []
    if os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            dados = list(reader)
    return dados

@app.on_event("startup")
def startup_event():
    print(">>> SERVIDOR INICIADO.")
    print(">>> O robô vai rodar sozinho às 10:00 e às 18:00.")

# Se você rodar o arquivo direto pelo python, ele inicia o uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)