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

# Configuração do logging
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

formatter = CustomFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("script_log.log")
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

def retry_operation(max_attempts: int = 3, delay: int = 1):
    """Decorator para retentar operações"""
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

def log_and_print(message: str):
    """Registra a mensagem no log e opcionalmente imprime no console."""
    logging.info(message)

def configurar_driver() -> webdriver:
    """Configura o driver do navegador"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("start-maximized")
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    return driver

def tratar_alerta(driver: webdriver) -> bool:
    """Trata alertas pendentes no navegador"""
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        logging.info(f"Alerta tratado: {alert_text}")
        return True
    except:
        return False

@retry_operation(max_attempts=3, delay=2)
def fazer_login(driver: webdriver, url: str, username: str, password: str) -> None:
    """Realiza o login na página com tratamento de erros melhorado"""
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        usuario_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtUsuario"))
        )
        usuario_input.clear()
        usuario_input.send_keys(username)
        senha_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pwdSenha"))
        )
        senha_input.clear()
        senha_input.send_keys(password)
        botao_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "Acessar"))
        )
        botao_login.click()
        if tratar_alerta(driver):
            raise Exception("Falha no login: Alerta de erro detectado")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#lnkControleProcessos > img"))
        ).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#divFiltro > div:nth-child(1) > a"))
        ).click()
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#tblProcessosDetalhado > tbody > tr:nth-child(1) > th:nth-child(6) > div > div:nth-child(2) > a > img"))
        ).click()
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logging.info(f"===== Logs de {obter_data_atual_formatada()} =====")
        logging.info("Iniciando script SEI...")
        logging.info("Login realizado com sucesso")
    except Exception as e:
        logging.error(f"Erro durante o login: {str(e)}")
        raise

def verificar_linha_sem_atribuicao(linha) -> bool:
    """Verifica se a linha não tem usuário atribuído com tratamento de erros"""
    try:
        celulas = linha.find_elements(By.TAG_NAME, "td")
        for celula in celulas:
            elementos_ancora = celula.find_elements(By.CLASS_NAME, "ancoraSigla")
            if elementos_ancora:
                return False
        return True
    except Exception as e:
        log_and_print(f"Erro ao atribuir tag: {str(e)}")
        return False

def verificar_ultima_pagina(driver: webdriver) -> bool:
    """Verifica se está na última página com verificação robusta"""
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "lnkInfraProximaPaginaInferior"))
        )
        return False
    except (TimeoutException, NoSuchElementException):
        return True

@retry_operation(max_attempts=2, delay=1)
def processar_pagina_atual(driver: webdriver, termos_tag: dict, contadores: dict, contadores_pagina: dict) -> None:
    """Processa a página atual"""
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.infraTable")))
    
    for termo in contadores_pagina:
        contadores_pagina[termo] = 0
        
    for termo_busca, acao in termos_tag.items():
        logging.info(f"Procurando por: {termo_busca}")
        xpath_termo = f"//td[contains(text(), '{termo_busca}')]"
        celulas_termo = driver.find_elements(By.XPATH, xpath_termo)
        
        for celula in celulas_termo:
            try:
                linha = celula.find_element(By.XPATH, "./..")
                
                # Verifica se o campo de atribuição está vazio
                try:
                    campo_atribuicao = linha.find_element(By.XPATH, ".//td[2]")
                    if campo_atribuicao.text.strip()!= "":
                        logging.info("Campo de atribuição não está vazio. Pulando linha.")
                        continue
                except Exception as e:
                    logging.warning(f"Erro ao verificar campo de atribuição: {str(e)}")
                    continue
                
                if not verificar_linha_sem_atribuicao(linha):
                    continue
                    
                try:
                    checkbox_div = linha.find_element(By.CSS_SELECTOR, "td:first-child div.infraCheckboxDiv")
                    checkbox = checkbox_div.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    
                    # Rola até o elemento
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    
                    # Clica no checkbox
                    driver.execute_script("arguments[0].click();", checkbox)
                    
                    # Aguarda o checkbox ser selecionado
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_selected(checkbox)
                    )
                    
                    contadores_pagina[termo_busca] += 1
                    logging.info(f"Checkbox selecionado com sucesso para: {termo_busca}")
                except Exception as e:
                    log_and_print(f"Erro ao interagir com checkbox: {str(e)}")
                    continue
            except Exception as e: 
                log_and_print(f"Erro ao processar linha: {str(e)}")
                continue
                
        if contadores_pagina[termo_busca] > 0:
            realizar_atribuicao(driver, acao)
            contadores[termo_busca] += contadores_pagina[termo_busca]

@retry_operation(max_attempts=2, delay=1)
def realizar_atribuicao(driver: webdriver, acao: dict) -> None:
    """Realiza a atribuição de marcadores"""
    try:
        logging.info("Iniciando processo de TAG")
        botao_atributo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#divComandos > a:nth-child(10) > img"))
        )
        botao_atributo.click()
        
        # Abre o dropdown
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#selMarcador"))
        )
        dropdown.click()
        
        # Tenta selecionar a opção usando diferentes abordagens
        try:
            # Primeira tentativa: usando XPath específico com o valor do tag do JSON
            #xpath_expression = f"//ul/li/a/label[contains(text(), '{acao['tag']}')]"
            xpath_expression = f"//ul/li/a/label[text() = '{acao['tag']}']"
            opcao = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath_expression))
            )
        except:
            try:
                # Segunda tentativa: usando JavaScript com o valor do tag do JSON
                script = f"""
                    var labels = document.querySelectorAll('label');
                    for(var i = 0; i < labels.length; i++) {{
                        if(labels[i].textContent.includes('{acao["tag"]}')) {{
                            labels[i].click();
                            return true;
                        }}
                    }}
                    return false;
                """
                success = driver.execute_script(script)
                if not success:
                    raise Exception(f"Não foi possível encontrar a opção {acao['tag']}")
            except:
                # Terceira tentativa: usando CSS Selector com o valor do atributo do JSON
                css_selector = f"label[class='dd-option-text']:contains('{acao['tag']}')"
                opcao = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
                )
                
        if 'opcao' in locals():
            opcao.click()
        
        # Aguarda a seleção ser processada
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.dd-select-loading"))
        )
        
        logging.info(f"Opção {acao['tag']} selecionada")
        
        botao_salvar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#sbmSalvar'))
        )
        botao_salvar.click()
        
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
    except Exception as e:
        log_and_print(f"Erro ao realizar atribuição: {str(e)}")
        raise

def realizar_atribuicoes(driver: webdriver, termos_tag: dict) -> dict:
    """Realiza as atribuições em todas as páginas com gestão de erros"""
    contadores = {termo: 0 for termo in termos_tag}
    contadores_pagina = {termo: 0 for termo in termos_tag}
    pagina_atual = 1
    while True:
        try:
            logging.info(f"\nProcessando página {pagina_atual}")
            processar_pagina_atual(driver, termos_tag, contadores, contadores_pagina)
            if verificar_ultima_pagina(driver):
                logging.info("Última página alcançada")
                break
            proximo_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "lnkInfraProximaPaginaInferior"))
            )
            proximo_link.click()
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            ) 
            pagina_atual += 1
        except Exception as e:
            log_and_print(f"Erro ao processar página {pagina_atual}: {str(e)}")
            if pagina_atual > 1:
                # Tenta continuar com a próxima página se não estiver na primeira
                continue
            else:
                break
    return contadores

def obter_data_atual_formatada():
    """Retorna a data e hora atual formatada"""
    agora = datetime.datetime.now()
    return agora.strftime('%A, %d de %B de %Y, às %H:%M:%S')

def fazer_logout(driver: webdriver) -> None:
    """Realiza o logout com tratamento de erros aprimorado"""
    try:
        # Verifica se ainda está logado
        try:
            botao_logout = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#lnkInfraSairSistema > img"))
            )
            botao_logout.click()
            logging.info("Logout realizado com sucesso")
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            logging.warning("Botão de logout não encontrado - usuário possivelmente já deslogado")
    except Exception as e:
        logging.error(f"Erro durante o logout: {str(e)}")
    finally:
        try:
            # Trata qualquer alerta pendente
            tratar_alerta(driver)
            driver.quit()
            logging.info("Driver fechado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao fechar o driver: {str(e)}")

def verificar_credenciais(url: str, username: str, password: str) -> None:
    """Verifica se as credenciais estão presentes e válidas"""
    if not url or not isinstance(url, str):
        raise ValueError("URL inválida ou não encontrada no arquivo.env")
    if not username or not isinstance(username, str):
        raise ValueError("USERNAME inválido ou não encontrado no arquivo.env")
    if not password or not isinstance(password, str):
        raise ValueError("PASSWORD inválida ou não encontrada no arquivo.env")

def validar_termos_tag(termos_tag: dict) -> None:
    """Valida o conteúdo do arquivo termos_acoes.json"""
    if not isinstance(termos_tag, dict) or len(termos_tag) == 0:
        raise ValueError("Arquivo termos_acoes.json vazio ou mal formatado.")
    for termo, acao in termos_tag.items():
        if not isinstance(termo, str) or not isinstance(acao, dict):
            raise ValueError(f"Entrada inválida no arquivo termos_acoes.json: {termo}")
        if "tag" not in acao or not isinstance(acao["tag"], str):
            raise ValueError(f"Tag ausente ou inválido para o termo: {termo}")

def main():
    driver = None
    try:
        # Carregar e verificar credenciais
        load_dotenv()
        url = os.getenv("SEI_URL")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        verificar_credenciais(url, username, password)

        # Carregar termos de busca
        try:
            with open("termos_acoes.json", "r", encoding="utf-8") as arquivo:
                termos_tag = json.load(arquivo)
                validar_termos_tag(termos_tag)
        except FileNotFoundError:
            raise FileNotFoundError("Arquivo termos_acoes.json não encontrado.")
        except json.JSONDecodeError:
            raise ValueError("Erro ao decodificar o arquivo termos_acoes.json. Verifique o formato JSON.")

        # Log dos termos carregados
        for termo, valores in termos_tag.items():
            logging.info(f"Termo: {termo}, Atributo: {valores['tag']}")

        # Configurar driver e realizar login
        driver = configurar_driver()
        fazer_login(driver, url, username, password)

        # Realizar atribuições
        contadores = realizar_atribuicoes(driver, termos_tag)

        # Resultados
        data_formatada = obter_data_atual_formatada()
        print(f"==== {data_formatada} ====")

        log_and_print("Script SEI executado com sucesso!")
        print("\nResumo dos marcadores-tags realizados:")
        for termo, contador in contadores.items():
            print(f"- {contador} marcadores para '{termo}'")
        print()
    except Exception as e:
        log_and_print(f"Erro durante a execução: {str(e)}")
        logging.error("Stacktrace completo:", exc_info=True)
    finally:
        if driver:
            fazer_logout(driver)

if __name__ == "__main__":
    main()
