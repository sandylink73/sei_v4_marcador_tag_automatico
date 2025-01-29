import locale
import json
import datetime
import time
import logging
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configuração do logging
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

formatter = CustomFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("script_log.log")
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Esta função registra a mensagem no log e a imprime no console.
# A linha print(message) está comentada para evitar a impressão no console.
def log_and_print(message):
    #print(message)
    logging.info(message)

# Configuração do webdriver
def configurar_driver():
    """Configura e retorna o driver do Chrome."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_script_timeout(10)
    return driver

def fazer_login(driver, url, username, password):
    """Realiza o login na página especificada."""
    driver.get(url)
    
    # Esperar até que a URL esteja completamente carregada
    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    
    # Esperar até que o campo de usuário esteja presente e enviar o nome de usuário
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtUsuario"))).send_keys(username)

    # Esperar até que o campo de senha esteja presente e enviar a senha
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pwdSenha"))).send_keys(password)

    # Esperar até que o botão de login esteja presente e clicável
    botao_login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "Acessar")))
    botao_login.click()

    # Aguardar a página de seleção de Processos
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#lnkControleProcessos > img"))).click()
    
    # Aguardar visualização detalhada
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#divFiltro > div:nth-child(1) > a"))).click()
    time.sleep(1.0)
    logging.info("")
    logging.info(f"===== Logs do dia =====")
    logging.info("Login realizado com sucesso")
    

def verificar_linha_sem_atribuicao(linha):
    """Verifica se a linha não tem usuário atribuído."""
    try:
        celulas = linha.find_elements(By.TAG_NAME, "td")
        for celula in celulas:
            elementos_ancora = celula.find_elements(By.CLASS_NAME, "ancoraSigla")
            if elementos_ancora:
                return False
        return True
    except Exception as e:
        log_and_print(f"Erro ao verificar atribuição: {str(e)}")
        #logging.error(f"Erro ao verificar atribuição: {str(e)}")
        return False

def verificar_ultima_pagina(driver):
    """Verifica se está na última página."""
    try:
        proximo_link = driver.find_element(By.ID, "lnkInfraProximaPaginaInferior")
        return False
    except NoSuchElementException:
        return True

def processar_pagina_atual(driver, termos_acoes, contadores, contadores_pagina):
    """Processa a página atual fazendo as atribuições necessárias."""
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.infraTable")))
    
    # Resetar contadores da página atual
    for termo in contadores_pagina:
        contadores_pagina[termo] = 0
    
    for termo_busca, acao in termos_acoes.items():
        logging.info(f"Procurando por: {termo_busca}")
        
        xpath_termo = f"//td[contains(text(), '{termo_busca}')]"
        celulas_termo = driver.find_elements(By.XPATH, xpath_termo)
        
        for celula in celulas_termo:
            try:
                linha = celula.find_element(By.XPATH, "./..")
                
                if not verificar_linha_sem_atribuicao(linha):
                    #print(f"Ignorando linha que já possui atribuição para: {termo_busca}")
                    continue
                
                try:
                    checkbox_div = linha.find_element(By.CSS_SELECTOR, "td:first-child div.infraCheckboxDiv")
                    checkbox = checkbox_div.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    
                    #print(f"Checkbox encontrado para: {termo_busca}")
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    time.sleep(0.3)
                    
                    driver.execute_script("arguments[0].click();", checkbox)
                    #print(f"Clique executado via JavaScript para: {termo_busca}")
                    time.sleep(0.3)
                    
                    if checkbox.is_selected():
                        #print(f"Checkbox confirmado como selecionado para: {termo_busca}")
                        contadores_pagina[termo_busca] += 1
                    else:
                        log_and_print(f"Checkbox não foi selecionado para: {termo_busca}")
                        #logging.error(f"Checkbox não foi selecionado para: {termo_busca}")
                    
                except Exception as e:
                    log_and_print(f"Erro ao interagir com checkbox: {str(e)}")
                    #logging.error(f"Erro ao interagir com checkbox: {str(e)}")
                    continue
            
            except Exception as e:
                log_and_print(f"Erro ao processar linha: {str(e)}")
                #logging.error(f"Erro ao processar linha: {str(e)}")
                continue

        if contadores_pagina[termo_busca] > 0:
            realizar_atribuicao(driver, acao)
            # Adicionar ao contador total
            contadores[termo_busca] += contadores_pagina[termo_busca]
            #print(f"Total acumulado para {termo_busca}: {contadores[termo_busca]}")

def realizar_atribuicao(driver, acao):
    """Realiza a atribuição para os itens selecionados."""
    try:
        #print(f"Iniciando processo de atribuição")
        logging.info(f"Iniciando processo de atribuição")
        botao_atributo = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#divComandos > a:nth-child(3) > img"))
        )
        botao_atributo.click()
        time.sleep(0.5)
        #print("Botão de atribuição clicado")
        logging.info("Botão de atribuição clicado")

        dropdown = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#selAtribuicao"))
        )
        dropdown.click()
        time.sleep(0.5)
        #print("Dropdown clicado")

        opcao = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f'//option[contains(text(), "{acao["atributo"]}")]'))
        )
        opcao.click()
        time.sleep(0.5)
        logging.info(f"Opção {acao['atributo']} selecionada") #Não retirar esta linha

        botao_salvar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#sbmSalvar'))
        )
        botao_salvar.click()
        time.sleep(1.0)
        #print("Alterações salvas")

    except Exception as e:
        log_and_print(f"Erro ao realizar atribuição: {str(e)}")

def realizar_atribuicoes(driver, termos_acoes):
    """Realiza as atribuições em todas as páginas."""
    contadores = {termo: 0 for termo in termos_acoes}  # Contador total
    contadores_pagina = {termo: 0 for termo in termos_acoes}  # Contador por página
    pagina_atual = 1
    
    while True:
        logging.info(f"\nProcessando página {pagina_atual}")
        processar_pagina_atual(driver, termos_acoes, contadores, contadores_pagina)
        
        if verificar_ultima_pagina(driver):
            logging.info("Última página alcançada")
            break
            
        try:
            proximo_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "lnkInfraProximaPaginaInferior"))
            )
            proximo_link.click()
            time.sleep(1.5)  # Aguardar carregamento da próxima página
            pagina_atual += 1
        except Exception as e:
            log_and_print(f"Erro ao navegar para próxima página: {str(e)}")
            break
    
    return contadores

def obter_data_atual_formatada():
    """Retorna a data e hora atual formatada."""
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    agora = datetime.datetime.now()
    return agora.strftime('%A, %d de %B de %Y, às %H:%M:%S')

def fazer_logout(driver):
    """Realiza o logout da aplicação."""
    try:
        botao_logout = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#lnkInfraSairSistema > img"))
        )
        botao_logout.click()
    finally:
        driver.quit()

def main():
    
    # Ler URL e credenciais do .env
    load_dotenv()
    url = os.getenv("SEI_URL")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    driver = configurar_driver()

    try:
        fazer_login(driver, url, username, password)
        
        # Lendo os termos de busca no arquivo JSON
        with open("termos_acoes.json", "r", encoding="utf-8") as arquivo:
            termos_acoes = json.load(arquivo)
        # Utilizando o dicionário
        for termo, valores in termos_acoes.items():
            logging.info(f"Termo: {termo}, Atributo: {valores['atributo']}")
        
        contadores = realizar_atribuicoes(driver, termos_acoes)

        # Imprimir resultados no terminal
        print("\n" + "="*50)
        print(obter_data_atual_formatada())
        log_and_print("Script SEI executado com sucesso!")
        print("\nResumo das atribuições realizadas:")
        for termo, contador in contadores.items():
            print(f"- {contador} atribuições para '{termo}'")
        print("="*50)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    finally:
        fazer_logout(driver)

if __name__ == "__main__":
    main()