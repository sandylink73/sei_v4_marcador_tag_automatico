# SEI versão 4 Multi-atribuidor automático de processos

Este projeto automatiza a atribuição de processos no Sistema Eletrônico de Informações (SEI) versão 4, utilizando Selenium WebDriver para Python.

Testado no ambiente de teste SEI versão 4.0.11 
* Módulo versão 3.3.0
* URL: https://sei.orgao1.tramita.processoeletronico.gov.br/
* Usuário e senha: usuariobasicoseiorgao101

## 🚀 Funcionalidades

- Login automatizado no sistema SEI
- Atribuição automática de processos para múltiplos usuários e múltiplos TIPOS de processo
- Contagem e relatório de atribuições realizadas
- Pode ser executado pelo cron (Linux, Macos) ou Agendador de Tarefas (Windows) em pré-determinados horários.

## 📋 Pré-requisitos

- Python 3.6 ou superior
- Google Chrome
- ChromeDriver compatível com sua versão do Chrome

### Bibliotecas Python necessárias
```bash
selenium
```

## 🔧 Instalação

1. Clone o repositório
```bash
git clone https://github.com/alemiti7/sei_v4_multi-atribuidor-automatico.git
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Configure o arquivo de credenciais
Crie um arquivo `credentials_v4.txt` com suas credenciais:
```
seu_usuario
sua_senha
```

## ⚙️ Configuração

O script pode ser configurado através do dicionário `termos_acoes` no arquivo principal. Exemplo:

```python
termos_acoes = {
    "Pessoal: Curso de Pós-Graduação": {"atributo": "ORGAO1"},
    "Material: Inventário de Material Permanente": {"atributo": "usuario1"},
    "Arrecadação: Receita": {"atributo": "usuariobasicoseiorgao101"},
}
```

## 🖥️ Uso

Execute o script principal:
```bash
python main.py
```

## 🔍 Funcionamento

O script realiza as seguintes operações:

1. Faz login no sistema SEI
2. Navega até a página de controle de processos
3. Para cada página:
   - Procura por processos que correspondam aos termos configurados
   - Verifica se os processos já possuem atribuição
   - Seleciona processos sem atribuição
   - Realiza a atribuição conforme configurado
4. Navega para a próxima página até atingir a última
5. Gera um relatório das atribuições realizadas
6. Realiza logout do sistema

## ⚠️ Elementos JavaScript

O script interage com elementos JavaScript em alguns pontos específicos:

1. Navegação entre páginas:
```html
<a id="lnkInfraProximaPaginaInferior" href="javascript:void(0);" onclick="infraAcaoPaginar('+',0,'Infra', null);">
```

2. Interações via Selenium:
```python
driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
driver.execute_script("arguments[0].click();", checkbox)
```

## 🛠️ Tecnologias Utilizadas

- Python
- Selenium WebDriver
- JavaScript (para interações com a página)
- Chrome WebDriver

## 📊 Logs e Monitoramento

O script fornece logs detalhados de suas operações, incluindo:
- Progresso da navegação entre páginas
- Contagem de atribuições por termo
- Erros e exceções encontrados
- Resumo final das operações realizadas e data atual

## 🤝 Contribuindo

Formas de contribuir:
- Sugerir melhorias e reportar bugs
- Compartilhar scripts de automação do SEI!

## ✒️ Autores

* ** Alexandre Mitsuru Nikaitow** - *Desenvolvimento Inicial* - https://github.com/alemiti7

📞 Contato
Alexandre
📧 alemiti@gmail.com
⌨️ com ❤️ por [@alemiti7]([https://github.com/alemiti7]) 😊

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE.md](LICENSE.md) para detalhes.
