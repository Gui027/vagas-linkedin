# scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import random 
import csv
import os
from dotenv import load_dotenv # <--- NOVO: Import para ler o .env local

# Carrega as variáveis do arquivo .env (se existir)
load_dotenv()

ARQUIVO_CSV = "vagas_consolidado.csv"

# --- PEGAR CREDENCIAIS DO AMBIENTE ---
# Se não achar no ambiente, retorna None e vai dar erro no login (segurança)
EMAIL_USER = os.getenv("LINKEDIN_EMAIL")
SENHA_USER = os.getenv("LINKEDIN_SENHA")

def carregar_historico():
    vagas_vistas = set()
    if os.path.exists(ARQUIVO_CSV):
        try:
            with open(ARQUIVO_CSV, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chave = (row["Vaga"], row["Empresa"])
                    vagas_vistas.add(chave)
        except Exception as e:
            print(f"Erro ao ler histórico: {e}")
    return vagas_vistas

def executar_raspagem():
    print(f"\n[{time.strftime('%H:%M:%S')}] Iniciando rotina automática...")
    
    # Verifica se as senhas existem antes de tentar abrir o Chrome
    if not EMAIL_USER or not SENHA_USER:
        print("ERRO CRÍTICO: Variáveis de ambiente LINKEDIN_EMAIL ou LINKEDIN_SENHA não configuradas.")
        return "Erro Configuração"

    # --- MODO INVISÍVEL ATIVADO ---
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080) 

    vagas_vistas = carregar_historico()
    novas_vagas = []

    # Login
    try:
        driver.get("https://www.linkedin.com/login")
        wait = WebDriverWait(driver, 10)
        usuario = wait.until(EC.presence_of_element_located((By.ID, "username")))
        
        # --- AQUI ESTÁ A PROTEÇÃO ---
        usuario.send_keys(EMAIL_USER) # Usa a variável, não o texto
        driver.find_element(By.ID, "password").send_keys(SENHA_USER) 
        
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)
    except Exception as e:
        print(f"Erro login: {e}")
        driver.quit()
        return "Erro Login"

    lista_urls = [
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22desenvolvedor%22%20AND%20%22jr%22%20&origin=GLOBAL_SEARCH_HEADER&sid=fgK&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22programador%22%20AND%20%22jr%22&origin=GLOBAL_SEARCH_HEADER&sid=!GQ&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22dev%22%20AND%20%22junior%22&origin=GLOBAL_SEARCH_HEADER&sid=JJU&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22react%22%20AND%20%22j%C3%BAnior%22&origin=GLOBAL_SEARCH_HEADER&sid=%3Bd(&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22java%22%20AND%20%22j%C3%BAnior%22&origin=GLOBAL_SEARCH_HEADER&sid=9Q)&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22java%22%20AND%20%22jr%22&origin=GLOBAL_SEARCH_HEADER&sid=%3ATI&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22desenvolvedor%22%20AND%20%22estagio%22&origin=GLOBAL_SEARCH_HEADER&sid=oVM&sortBy=%22date_posted%22'
    ]

    try:
        for i, url in enumerate(lista_urls):
            print(f"> Processando {i+1}/{len(lista_urls)}...")
            driver.get(url)
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))

            posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-view-name="feed-full-update"]')
            
            c = 0
            for post in posts:
                if c >= 3: break
                try:
                    card = post.find_element(By.CSS_SELECTOR, 'a[data-view-name="feed-job-card-entity"]')
                    link = card.get_attribute("href")
                    ps = card.find_elements(By.TAG_NAME, "p")
                    titulo = ps[0].text.strip() if len(ps) >= 1 else "N/A"
                    empresa = ps[1].text.strip() if len(ps) >= 2 else "N/A"
                    
                    if (titulo, empresa) in vagas_vistas: continue
                    
                    try:
                        txt = post.find_element(By.CSS_SELECTOR, 'div[data-view-name="feed-commentary"]').text.replace("\n", " ")[:200]
                    except: txt = "N/A"

                    novas_vagas.append({"Origem_Busca": f"Link {i+1}", "Empresa": empresa, "Vaga": titulo, "Link": link, "Texto do Post": txt})
                    vagas_vistas.add((titulo, empresa))
                    c += 1
                except: continue
            time.sleep(random.uniform(3, 5))

    except Exception as e:
        print(f"Erro raspagem: {e}")
    finally:
        driver.quit()

    if novas_vagas:
        file_exists = os.path.exists(ARQUIVO_CSV)
        with open(ARQUIVO_CSV, mode='a' if file_exists else 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["Origem_Busca", "Empresa", "Vaga", "Link", "Texto do Post"])
            if not file_exists: writer.writeheader()
            writer.writerows(novas_vagas)
        print(f"[SUCESSO] {len(novas_vagas)} novas vagas adicionadas.")
    else:
        print("[INFO] Nenhuma vaga nova.")