import locale
import json
import datetime
import time
import logging
import random
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from functools import wraps

# Configuração inicial do sistema de logs e localização
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Classe personalizada para formatar logs
class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

# Configuração do handler de logs para gravar em arquivo
formatter = CustomFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("script_log.log")
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Decorador para retentar operações falhas
def retry_operation(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(f"Tentativa {attempt + 1} falhou: {str(e)}. Retentando em {delay} segundos...")
                        time.sleep(delay)
                    else:
                        logging.error(f"Todas as {max_attempts} tentativas falharam para {func.__name__}")
                        raise last_exception
        return wrapper
    return decorator

# Função para registrar mensagens no log e opcionalmente imprimi-las no console
def log_and_print(message):
    logging.info(message)

# Configuração do driver do Selenium com opções específicas
def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa o navegador em modo headless (sem interface gráfica)
    chrome_options.add_argument("--disable-gpu")  # Desativa a aceleração de GPU
    chrome_options.add_argument("--no-sandbox")  # Desativa o sandbox do Chrome (útil em ambientes como Docker)
    chrome_options.add_argument("--disable-dev-shm-usage")  # Usa /tmp para armazenamento temporário
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Desativa recursos relacionados à automação
    chrome_options.add_argument("--disable-popup-blocking")  # Desativa o bloqueio de pop-ups
    chrome_options.add_argument("--disable-extensions")  # Desativa extensões que podem interferir na navegação
    chrome_options.add_argument("--disable-infobars")  # Remove barras de informações sobre automação
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Remove notificações de automação
    chrome_options.add_argument("start-maximized")  # Maximiza a janela do navegador

    # Rotação de user-agent para simular diferentes navegadores e dispositivos
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    # Inicializa o WebDriver com as opções configuradas
    driver = webdriver.Chrome(options=chrome_options)

    # Remove a flag navigator.webdriver para evitar detecção de automação
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    return driver

# Trata alertas que aparecem durante a navegação
def tratar_alerta(driver):
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        logging.info(f"Alerta tratado: {alert_text}")
        return True
    except Exception:
        logging.info("Nenhum alerta encontrado.")
        return False

# Realiza o login no sistema com tratamento de erros
@retry_operation(max_attempts=3, delay=2)
def fazer_login(driver, url, username, password):
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        usuario_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtUsuario")))
        usuario_input.clear()
        usuario_input.send_keys(username)
        senha_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pwdSenha")))
        senha_input.clear()
        senha_input.send_keys(password)
        botao_login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "Acessar")))
        botao_login.click()

        if tratar_alerta(driver):
            raise Exception("Falha no login: Alerta de erro detectado.")

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#lnkControleProcessos > img"))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#divFiltro > div:nth-child(1) > a"))).click()
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#tblProcessosDetalhado > tbody > tr:nth-child(1) > th:nth-child(6) > div > div:nth-child(2) > a > img"))).click()
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        logging.info(f"===== Logs de {obter_data_atual_formatada()} =====")
        logging.info("Iniciando script SEI...")
        logging.info("Login realizado com sucesso")
    except Exception as e:
        logging.error(f"Erro durante o login: {str(e)}")
        raise

# Verifica se uma linha não possui atribuição
def verificar_linha_sem_atribuicao(linha):
    try:
        celulas = linha.find_elements(By.TAG_NAME, "td")
        for celula in celulas:
            elementos_ancora = celula.find_elements(By.CLASS_NAME, "ancoraSigla")
            if elementos_ancora:
                return False
        return True
    except Exception as e:
        log_and_print(f"Erro ao verificar linha sem atribuição: {str(e)}")
        return False

# Verifica se está na última página da tabela
def verificar_ultima_pagina(driver):
    try:
        elemento = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "lnkInfraProximaPaginaInferior")))
        return False
    except (TimeoutException, NoSuchElementException):
        return True

# Processa a página atual, verificando termos e realizando ações
@retry_operation(max_attempts=2, delay=1)
def processar_pagina_atual(driver, termos_acoes, contadores, contadores_pagina):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.infraTable")))
    for termo in contadores_pagina:
        contadores_pagina[termo] = 0
    for termo_busca, acao in termos_acoes.items():
        logging.info(f"Procurando por: {termo_busca}")
        xpath_termo = f"//td[text() = '{termo_busca}']"
        celulas_termo = driver.find_elements(By.XPATH, xpath_termo)
        for celula in celulas_termo:
            try:
                linha = celula.find_element(By.XPATH, "./..")
                if not verificar_linha_sem_atribuicao(linha):
                    continue
                try:
                    checkbox_div = linha.find_element(By.CSS_SELECTOR, "td:first-child div.infraCheckboxDiv")
                    checkbox = checkbox_div.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    WebDriverWait(driver, 7).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    driver.execute_script("arguments[0].click();", checkbox)
                    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    if checkbox.is_selected():
                        contadores_pagina[termo_busca] += 1
                    else:
                        log_and_print(f"Checkbox não foi selecionado para: {termo_busca}")
                except Exception as e:
                    log_and_print(f"Erro ao interagir com checkbox: {str(e)}")
                    continue
            except Exception as e:
                log_and_print(f"Erro ao processar linha: {str(e)}")
                continue
        if contadores_pagina[termo_busca] > 0:
            realizar_atribuicao(driver, acao)
            contadores[termo_busca] += contadores_pagina[termo_busca]

# Realiza a atribuição dos itens selecionados
@retry_operation(max_attempts=2, delay=1)
def realizar_atribuicao(driver, acao):
    try:
        logging.info("Iniciando processo de atribuição")
        botao_atributo = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#divComandos > a:nth-child(3) > img")))
        botao_atributo.click()
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        logging.info("Botão de atribuição clicado")
        dropdown = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#selAtribuicao")))
        dropdown.click()
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        opcao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f'//option[text() = "{acao["atributo"]}"]')))
        opcao.click()
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        logging.info(f"Opção {acao['atributo']} selecionada")
        botao_salvar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#sbmSalvar')))
        botao_salvar.click()
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except Exception as e:
        log_and_print(f"Erro ao realizar atribuição: {str(e)}")
        raise

# Realiza as atribuições em todas as páginas disponíveis
def realizar_atribuicoes(driver, termos_acoes):
    contadores = {termo: 0 for termo in termos_acoes}
    contadores_pagina = {termo: 0 for termo in termos_acoes}
    pagina_atual = 1
    while True:
        try:
            logging.info(f"\nProcessando página {pagina_atual}")
            processar_pagina_atual(driver, termos_acoes, contadores, contadores_pagina)
            if verificar_ultima_pagina(driver):
                logging.info("Última página alcançada")
                break
            proximo_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "lnkInfraProximaPaginaInferior")))
            proximo_link.click()
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            pagina_atual += 1
        except Exception as e:
            log_and_print(f"Erro ao processar página {pagina_atual}: {str(e)}")
            if pagina_atual > 1:
                continue
            else:
                break
    return contadores

# Retorna a data e hora atual formatada
def obter_data_atual_formatada():
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    agora = datetime.datetime.now()
    return agora.strftime('%A, %d de %B de %Y, às %H:%M:%S')

# Realiza o logout do sistema
def fazer_logout(driver):
    try:
        try:
            botao_logout = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#lnkInfraSairSistema > img")))
            botao_logout.click()
            logging.info("Logout realizado com sucesso")
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            logging.warning("Botão de logout não encontrado - usuário possivelmente já deslogado")
    except Exception as e:
        logging.error(f"Erro durante o logout: {str(e)}")
    finally:
        try:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                logging.info("Alerta fechado durante logout")
            except:
                pass
            driver.quit()
            logging.info("Driver fechado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao fechar o driver: {str(e)}")

# Verifica se as credenciais estão presentes e válidas
def verificar_credenciais(url, username, password):
    if not url or not isinstance(url, str):
        raise ValueError("URL inválida ou não encontrada no arquivo .env")
    if not username or not isinstance(username, str):
        raise ValueError("USERNAME inválido ou não encontrado no arquivo .env")
    if not password or not isinstance(password, str):
        raise ValueError("PASSWORD inválida ou não encontrada no arquivo .env")

# Valida o conteúdo do arquivo de termos e ações
def validar_termos_acoes(termos_acoes):
    if not isinstance(termos_acoes, dict) or len(termos_acoes) == 0:
        raise ValueError("Arquivo termos_acoes.json vazio ou mal formatado.")
    for termo, acao in termos_acoes.items():
        if not isinstance(termo, str) or not isinstance(acao, dict):
            raise ValueError(f"Entrada inválida no arquivo termos_acoes.json: {termo}")
        if "atributo" not in acao or not isinstance(acao["atributo"], str):
            raise ValueError(f"Atributo ausente ou inválido para o termo: {termo}")

# Função principal que coordena a execução do script
def main():
    driver = None
    try:
        load_dotenv()
        url = os.getenv("SEI_URL")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        verificar_credenciais(url, username, password)

        try:
            with open("termos_acoes.json", "r", encoding="utf-8") as arquivo:
                termos_acoes = json.load(arquivo)
                validar_termos_acoes(termos_acoes)
        except FileNotFoundError:
            raise FileNotFoundError("Arquivo termos_acoes.json não encontrado.")
        except json.JSONDecodeError:
            raise ValueError("Erro ao decodificar o arquivo termos_acoes.json. Verifique o formato JSON.")

        for termo, valores in termos_acoes.items():
            logging.info(f"Termo: {termo}, Atributo: {valores['atributo']}")

        driver = configurar_driver()
        fazer_login(driver, url, username, password)
        contadores = realizar_atribuicoes(driver, termos_acoes)

        # Formatação e apresentação de data
        data_formatada = obter_data_atual_formatada()
        print(f"==== {data_formatada} ====")

        log_and_print("Script SEI executado com sucesso!")
        print("\nResumo das atribuições realizadas:")
        for termo, contador in contadores.items():
            print(f"- {contador} atribuições para '{termo}'")
        #print("="*50)
        print()
        
    except Exception as e:
        log_and_print(f"Erro durante a execução: {str(e)}")
        logging.error("Stacktrace completo:", exc_info=True)
    finally:
        if driver:
            fazer_logout(driver)

if __name__ == "__main__":
    main()
