from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import executar_raspagem, ARQUIVO_CSV
import csv
import os
import uvicorn

app = FastAPI(title="API Vagas LinkedIn - Agendada")

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

scheduler.add_job(executar_raspagem, 'cron', hour=10, minute=0, id="scrape_10")
scheduler.add_job(executar_raspagem, 'cron', hour=15, minute=59, id="scrape_1559")

scheduler.start()

@app.get("/")
def status():
    jobs = scheduler.get_jobs()
    return {
        "sistema": "Online",
        "agendamento": "Automático às 10:00 e 15:59 (America/Sao_Paulo)",
        "proximas_execucoes": [
            {"id": j.id, "next_run_time": str(j.next_run_time)}
            for j in jobs
        ]
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
    print(">>> O robô vai rodar sozinho às 10:00 e às 15:59 (America/Sao_Paulo).")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
