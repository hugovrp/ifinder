import fitz  
import requests
from agno.tools import tool
from bs4 import BeautifulSoup
from markdownify import markdownify as md 

@tool(name='read_pdf', 
      description='Abre um arquivo .pdf e retorna o seu conteúdo em markdown. Útil para ler informações de buscas que retornam um .pdf, p.ex.: Cardápio, Calendário, Editais, etc.')
def read_pdf(path):
    """
        Abre um arquivo PDF a partir de um URL e extrai seu conteúdo textual,
        convertendo-o para o formato Markdown para facilitar a análise pelo agente de IA.

        Esta ferramenta é crucial quando uma busca (como 'site_search') retorna um link direto para um 
        documento (.pdf) que contém a informação necessária (ex: Editais, Cardápios, Calendários Acadêmicos).

        Args:
            path (str): A URL completa (absoluta) do arquivo PDF a ser acessado.
        
        Returns:
            str: O texto extraído do PDF no formato Markdown. Se a leitura falhar, retorna uma string de erro.
    """
    doc = fitz.open(path)
    text = ""

    for page in doc:
        text += page.get_text()

    markdown = md(text)
    return markdown