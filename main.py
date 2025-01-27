import locale
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
    driver.find_element(By.ID, "txtUsuario").send_keys(username)
    driver.find_element(By.ID, "pwdSenha").send_keys(password)
    botao_login = driver.find_element(By.ID, "Acessar")
    botao_login.click()
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#lnkControleProcessos > img"))).click()
    WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#divFiltro > div:nth-child(1) > a"))).click()
    time.sleep(1.0)

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
        print(f"Erro ao verificar atribuição: {str(e)}")
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
        print(f"Procurando por: {termo_busca}")
        
        xpath_termo = f"//td[contains(text(), '{termo_busca}')]"
        celulas_termo = driver.find_elements(By.XPATH, xpath_termo)
        
        for celula in celulas_termo:
            try:
                linha = celula.find_element(By.XPATH, "./..")
                
                if not verificar_linha_sem_atribuicao(linha):
                    print(f"Ignorando linha que já possui atribuição para: {termo_busca}")
                    continue
                
                try:
                    checkbox_div = linha.find_element(By.CSS_SELECTOR, "td:first-child div.infraCheckboxDiv")
                    checkbox = checkbox_div.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                    
                    print(f"Checkbox encontrado para: {termo_busca}")
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    time.sleep(0.3)
                    
                    driver.execute_script("arguments[0].click();", checkbox)
                    print(f"Clique executado via JavaScript para: {termo_busca}")
                    time.sleep(0.3)
                    
                    if checkbox.is_selected():
                        print(f"Checkbox confirmado como selecionado para: {termo_busca}")
                        contadores_pagina[termo_busca] += 1
                    else:
                        print(f"Checkbox não foi selecionado para: {termo_busca}")
                    
                except Exception as e:
                    print(f"Erro ao interagir com checkbox: {str(e)}")
                    continue
            
            except Exception as e:
                print(f"Erro ao processar linha: {str(e)}")
                continue

        if contadores_pagina[termo_busca] > 0:
            realizar_atribuicao(driver, acao)
            # Adicionar ao contador total
            contadores[termo_busca] += contadores_pagina[termo_busca]
            print(f"Total acumulado para {termo_busca}: {contadores[termo_busca]}")

def realizar_atribuicao(driver, acao):
    """Realiza a atribuição para os itens selecionados."""
    try:
        print(f"Iniciando processo de atribuição")
        
        botao_atributo = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#divComandos > a:nth-child(3) > img"))
        )
        botao_atributo.click()
        time.sleep(0.5)
        print("Botão de atribuição clicado")

        dropdown = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#selAtribuicao"))
        )
        dropdown.click()
        time.sleep(0.5)
        print("Dropdown clicado")

        opcao = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f'//option[contains(text(), "{acao["atributo"]}")]'))
        )
        opcao.click()
        time.sleep(0.5)
        print(f"Opção {acao['atributo']} selecionada")

        botao_salvar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#sbmSalvar'))
        )
        botao_salvar.click()
        time.sleep(1.0)
        print("Alterações salvas")

    except Exception as e:
        print(f"Erro ao realizar atribuição: {str(e)}")

def realizar_atribuicoes(driver, termos_acoes):
    """Realiza as atribuições em todas as páginas."""
    contadores = {termo: 0 for termo in termos_acoes}  # Contador total
    contadores_pagina = {termo: 0 for termo in termos_acoes}  # Contador por página
    pagina_atual = 1
    
    while True:
        print(f"\nProcessando página {pagina_atual}")
        processar_pagina_atual(driver, termos_acoes, contadores, contadores_pagina)
        
        if verificar_ultima_pagina(driver):
            print("Última página alcançada")
            break
            
        try:
            proximo_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "lnkInfraProximaPaginaInferior"))
            )
            proximo_link.click()
            time.sleep(1.5)  # Aguardar carregamento da próxima página
            pagina_atual += 1
        except Exception as e:
            print(f"Erro ao navegar para próxima página: {str(e)}")
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
    url = "https://sei.orgao1.tramita.processoeletronico.gov.br/"
    username = ""
    password = ""

    # Ler as credenciais do arquivo
    with open("credentials_v4.txt", "r") as file:
        username = file.readline().strip()
        password = file.readline().strip()

    driver = configurar_driver()

    try:
        fazer_login(driver, url, username, password)
        
        termos_acoes = {
            "Pessoal: Curso de Pós-Graduação": {"atributo": "usuariobasicoseiorgao101"},
            "Material: Inventário de Material Permanente": {"atributo": "usuario1"},
            "Arrecadação: Receita": {"atributo": "usuariobasicoseiorgao101"},
        }

        contadores = realizar_atribuicoes(driver, termos_acoes)

        # Imprimir resultados no terminal
        print("\n" + "="*50)
        print(obter_data_atual_formatada())
        print("Script SEI executado com sucesso!")
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
