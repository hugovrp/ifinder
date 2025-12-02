from agno.tools import tool
from bs4 import BeautifulSoup
import requests

BASE_URL = 'https://www.ifsudestemg.edu.br/barbacena'

# Funções que o Agente usará. 

''' 
    Usa o decorator @Tool para transformar uma função Python comum em uma ferramenta 
    formal que o LLM consegue entender e usar.
'''

@tool(name='open_link', 
      description='Abre um URL e retorna o texto principal da página. Útil para ler o conteúdo de uma notícia ou página específica.')
def open_link(url: str) -> str:
    '''

    Arg:
        url (str): Link da página a ser aberta.
    '''
    try:
        full_url = f"{BASE_URL}/{url.lstrip('/')}"
        
        response = requests.get(full_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extrai somente o texto visual
        text = soup.get_text(separator='\n', strip=True)
        if not text:
            return 'Erro ao acessar conteúdo da url {url}.'
        
        return text 
    
    except Exception as e: 
        return f'Erro ao acessar o link {url}: {e}'

@tool(name='site_search', 
      description='Realiza uma busca por um termo específico no site do Campus Barbacena. Retorna uma lista de títulos e URLs.')
def site_search(query: str) -> str:
    return ''