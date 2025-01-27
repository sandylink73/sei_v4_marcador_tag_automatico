# SEI versão 4 Multi-atribuidor automático de processos

Este projeto automatiza a atribuição de processos no Sistema Eletrônico de Informações (SEI) versão 4, utilizando Selenium WebDriver para Python.

## 🚀 Funcionalidades

- Login automatizado no sistema SEI
- Navegação automática entre páginas de processos
- Atribuição automática de processos baseada em critérios específicos
- Processamento de múltiplas páginas
- Contagem e relatório de atribuições realizadas

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
git clone https://github.com/seu-usuario/sei-automation.git
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
- Resumo final das operações realizadas

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## ✒️ Autores

* ** Alexandre Mitsuru Nikaitow** - *Desenvolvimento Inicial* - https://github.com/alemiti7
  

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE.md](LICENSE.md) para detalhes

## 🎁 Expressões de Gratidão

* Compartilhe este projeto 📢
* Convide alguém da equipe para uma café ☕ 
* Um agradecimento publicamente 🤓

---
⌨️ com ❤️ por [seu-usuario](https://github.com/seu-usuario) 😊
