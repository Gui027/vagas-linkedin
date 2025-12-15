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
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

# ===== Config =====
DATA_DIR = os.getenv("DATA_DIR", ".")  # em prod você pode setar /data se tiver disco
os.makedirs(DATA_DIR, exist_ok=True)

ARQUIVO_CSV = os.path.join(DATA_DIR, "vagas_consolidado.csv")

EMAIL_USER = os.getenv("LINKEDIN_EMAIL")
SENHA_USER = os.getenv("LINKEDIN_SENHA")

FIELDNAMES = ["Origem_Busca", "Empresa", "Vaga", "Link", "Texto do Post"]


def agora_sp() -> str:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%H:%M:%S")


def garantir_csv_com_header():
    """Garante que o CSV existe com cabeçalho (ajuda no debug)."""
    if not os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def carregar_historico():
    vagas_vistas = set()
    if os.path.exists(ARQUIVO_CSV):
        try:
            with open(ARQUIVO_CSV, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # pode existir header vazio no início; protege
                    vaga = (row.get("Vaga") or "").strip()
                    emp = (row.get("Empresa") or "").strip()
                    if vaga and emp:
                        vagas_vistas.add((vaga, emp))
        except Exception as e:
            print(f"Erro ao ler histórico: {e}")
    return vagas_vistas


def salvar_debug_html(prefixo: str, html: str):
    """Salva HTML em arquivo para investigar bloqueio/challenge/login."""
    try:
        path = os.path.join(DATA_DIR, f"{prefixo}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   !! DEBUG HTML salvo em: {path}")
    except Exception as e:
        print(f"   !! Falha ao salvar debug HTML: {e}")


def criar_driver():
    chrome_options = Options()

    # Headless moderno
    chrome_options.add_argument("--headless=new")

    # Estabilidade em container
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Ajuda layout do LinkedIn
    chrome_options.add_argument("--window-size=1920,1080")

    # Log mais limpo
    chrome_options.add_argument("--log-level=3")

    # (Opcional) reduzir "cara de automação"
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def executar_raspagem():
    print(f"\n[{agora_sp()}] Iniciando rotina automática...")

    if not EMAIL_USER or not SENHA_USER:
        print("ERRO CRÍTICO: Variáveis LINKEDIN_EMAIL ou LINKEDIN_SENHA não configuradas.")
        return "Erro Configuração"

    # garante arquivo (para /vagas não ficar dependendo de ter achado algo)
    garantir_csv_com_header()

    driver = criar_driver()
    wait = WebDriverWait(driver, 15)

    vagas_vistas = carregar_historico()
    novas_vagas = []

    # ===== Login =====
    try:
        driver.get("https://www.linkedin.com/login")

        usuario = wait.until(EC.presence_of_element_located((By.ID, "username")))
        usuario.clear()
        usuario.send_keys(EMAIL_USER)

        senha = driver.find_element(By.ID, "password")
        senha.clear()
        senha.send_keys(SENHA_USER)

        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        # espera algo pós-login carregar
        time.sleep(8)

        print("URL pós-login:", driver.current_url)
        print("TITLE pós-login:", driver.title)

        # se voltar pra login ou cair em challenge/checkpoint, salva HTML e aborta
        if "login" in driver.current_url or "checkpoint" in driver.current_url or "challenge" in driver.current_url:
            salvar_debug_html("debug_after_login", driver.page_source)
            driver.quit()
            return "Bloqueio/Challenge/Login"

    except Exception as e:
        print(f"Erro login: {e}")
        salvar_debug_html("debug_login_exception", driver.page_source)
        driver.quit()
        return "Erro Login"

    lista_urls = [
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22desenvolvedor%22%20AND%20%22jr%22%20&origin=GLOBAL_SEARCH_HEADER&sid=fgK&sortBy=%22date_posted%22',
        'https://www.linkedin.com/search/results/content/?contentType=%22jobs%22&keywords=%22estagio%22&origin=GLOBAL_SEARCH_HEADER&sid=ovZ&sortBy=%22date_posted%22',
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
            time.sleep(random.uniform(2, 3))

            print("   URL atual:", driver.current_url)
            print("   TITLE atual:", driver.title)

            # espera o feed aparecer
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-view-name="feed-full-update"]')))
            except Exception:
                print("   !! feed-full-update não apareceu")
                salvar_debug_html(f"debug_search_{i+1}", driver.page_source)
                continue

            # scroll
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))

            posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-view-name="feed-full-update"]')
            print(f"   -> posts encontrados: {len(posts)}")

            if len(posts) == 0:
                salvar_debug_html(f"debug_posts0_{i+1}", driver.page_source)
                continue

            c = 0
            for post in posts:
                if c >= 3:
                    break

                try:
                    card = post.find_element(By.CSS_SELECTOR, 'a[data-view-name="feed-job-card-entity"]')
                    link = card.get_attribute("href")

                    ps = card.find_elements(By.TAG_NAME, "p")
                    titulo = ps[0].text.strip() if len(ps) >= 1 else "N/A"
                    empresa = ps[1].text.strip() if len(ps) >= 2 else "N/A"

                    if (titulo, empresa) in vagas_vistas:
                        continue

                    try:
                        txt = post.find_element(By.CSS_SELECTOR, 'div[data-view-name="feed-commentary"]').text.replace("\n", " ")[:200]
                    except Exception:
                        txt = "N/A"

                    novas_vagas.append({
                        "Origem_Busca": f"Link {i+1}",
                        "Empresa": empresa,
                        "Vaga": titulo,
                        "Link": link,
                        "Texto do Post": txt
                    })

                    vagas_vistas.add((titulo, empresa))
                    c += 1

                except Exception:
                    # se o seletor do card mudar, salva um html pra investigar
                    continue

            time.sleep(random.uniform(2, 4))

    except Exception as e:
        print(f"Erro raspagem: {e}")
        salvar_debug_html("debug_raspagem_exception", driver.page_source)
    finally:
        driver.quit()

    if novas_vagas:
        file_exists = os.path.exists(ARQUIVO_CSV)
        with open(ARQUIVO_CSV, mode='a' if file_exists else 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerows(novas_vagas)

        print(f"[SUCESSO] {len(novas_vagas)} novas vagas adicionadas.")
        return f"OK: {len(novas_vagas)}"
    else:
        print("[INFO] Nenhuma vaga nova.")
        return "OK: 0"
