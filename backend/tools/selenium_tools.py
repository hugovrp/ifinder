from agno.tools import tool
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Código base do site do Instituto Federal - Campus Barbacena
BASE_URL = 'https://www.ifsudestemg.edu.br'

@tool(
    name='open_link_in_selenium',
    description='Abre uma URL usando um navegador real (Selenium/Chrome) e retorna o HTML da página, incluindo conteúdo carregado por JavaScript. Use esta ferramenta quando open_link não funcionar ou quando for necessário carregar conteúdo dinâmico.')
def open_link_in_selenium(url: str) -> dict:
    """
        Abre uma página web utilizando um navegador real controlado pelo Selenium (Google Chrome em modo headless).
        Esta ferramenta deve ser utilizada quando o conteúdo da página é gerado dinamicamente via JavaScript, 
        o que não pode ser obtido apenas com requisições HTTP simples usando a biblioteca requests.

        Args:
            url (str): URL completa da página que deverá ser aberta no navegador.

        Returns:
            dict: retorna o HTML final do DOM após o carregamento completo da página ou mensagem detalhando o erro ocorrido.

        Obs: O navegador é executado em modo headless (sem interface gráfica).
    """
     # Aceita URL absoluta ou relativa
    if url.startswith("http://") or url.startswith("http"):
        full_url = url
    else:
        full_url = f"{BASE_URL.rstrip('/')}/{url.lstrip('/')}"

    # Configuração do navegador Chrome, executa-o em modo headless (sem interface gráfica)
    options = Options()
    options.add_argument('--headless=new')

    # Baixa e inicializa o ChromeDriver compatível com o Google Chrome instalado na máquina
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # O Selenium espera até que o evento load seja disparado (documento carregou)
    driver.get(full_url)

    # Retorna o DOM atual do navegador, em HTML.
    html = driver.page_source

    # Fecha a janela do navegador e finaliza o processo do ChromeDriver, 
    # liberando todos os recursos de memória utilizados
    driver.quit()

    # Limita o tamanho do HTML para evitar sobrecarga no LLM
    html = html[:20000]
    return {'html': html}