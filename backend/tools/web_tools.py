from agno.tools import tool
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Código base do site do Instituto Federal - Campus Barbacena
BASE_URL = 'https://www.ifsudestemg.edu.br'


''' Funções que o Agente usará. 
    Usa o decorator @Tool para transformar uma função Python comum em uma ferramenta 
    formal que o LLM consegue entender e usar.
'''

@tool(name='open_link', 
      description='Abre um URL e retorna o texto principal da página. Útil para ler o conteúdo de uma notícia ou página específica.')
def open_link(url: str, full_html: bool) -> dict:
    '''
    Abre uma página web e retorna o conteúdo textual. 
    A URL pode ser fornecida de forma absoluta ou relativa ao domínio padrão do Campus Barbacena.
    A função é utilizada pelo agente de IA para recuperar informações do site institucional, 
    permitindo que o modelo obtenha dados diretamente das páginas.

    Args:
        url (str): A URL da página a ser acessada.
        full_html (bool): Se True, retorna o HTML completo da página. Se False, retorna apenas o texto visível, removendo scripts e estilos.
    
    Returns:
        dict : texto extraído da página, com no máximo 12.000 caracteres ou uma mensagem de erro.
    '''
    try:
        # Aceita URL absoluta ou relativa
        if url.startswith("http://") or url.startswith("http"):
            full_url = url
        else:
            full_url = f"{BASE_URL.rstrip('/')}/{url.lstrip('/')}"
        
        response = requests.get(full_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        if full_html == False:
            # Remove scripts e CSS
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Extrai somente o texto visual
            text = soup.get_text(separator='\n', strip=True)
            if not text:
                return {"error": f"Erro ao acessar conteúdo da URL {url}."}
        
            text = text[:12000]  # Tamanho máximo seguro
            return {'html': text}
    
        return {'html': soup}
        
    except Exception as e:
        return {"error": f"Erro ao acessar a URL {url}."}


@tool(name='site_search', 
      description='Realiza uma busca por um termo específico no site do Campus Barbacena. Retorna uma lista de títulos e URLs.')
def site_search(query: str) -> str:
    return ''