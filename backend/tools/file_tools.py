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
        convertendo-o para o formato Markdown.

        Args:
            path (str): A URL completa (absoluta) do arquivo PDF a ser acessado.
        
        Returns:
            str: O texto extraído do PDF no formato Markdown. Se a leitura falhar, retorna uma string de erro detalhada.
    """
    try:
        # Baixa o conteúdo binário do arquivo PDF da internet
        response = requests.get(path, timeout=30)
        response.raise_for_status()

        doc = fitz.open(stream=response.content, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        markdown = md(text)
        return markdown
    except requests.exceptions.RequestException as e:
        return f"Erro de rede ao tentar acessar o PDF. Verifique se o link está funcionando: {path}. Erro: {e}"
    except Exception as e:
        return f"Erro ao processar o arquivo PDF: {e}"