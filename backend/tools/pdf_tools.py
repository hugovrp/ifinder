import os
import fitz  
import requests
from agno.tools import tool
from bs4 import BeautifulSoup
from markdownify import markdownify as md 

BASE_URL = 'https://www.ifsudestemg.edu.br'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

@tool(name='read_pdf', 
      description='Abre um arquivo .pdf e retorna o seu conteúdo em markdown. Útil para ler informações de buscas que retornam um .pdf, p.ex.: Cardápio, Calendário, Editais, etc.')
def read_pdf(path):
    """
        Abre um arquivo PDF local ou a partir de um URL e extrai seu conteúdo textual,
        convertendo-o para o formato Markdown para facilitar a análise pelo agente de IA.

        Esta ferramenta é crucial quando uma busca (como 'site_search') retorna um link direto para um 
        documento (.pdf) que contém a informação necessária (ex: Editais, Cardápios, Calendários Acadêmicos).

        Args:
            path (str): A URL completa (absoluta) do arquivo PDF a ser acessado.

        Returns:
            str: O texto extraído do PDF no formato Markdown. Se a leitura falhar, retorna uma string de erro.
    """
    full_url = path if path.startswith('http') else f"https://www.ifsudestemg.edu.br{path}"

    try:
        if not os.path.exists(path):
            # Baixa o conteúdo binário do arquivo PDF da internet
            response = requests.get(full_url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            doc = fitz.open(stream=response.content, filetype="pdf")
        else :
            doc = fitz.open(path, filetype="pdf")

        text = ""

        for page in doc:
            text += page.get_text()

        markdown = md(text)
        return markdown
    except requests.exceptions.RequestException as e:
        return f"Erro de rede ao tentar acessar o PDF. Verifique se o link está funcionando: {path}. Erro: {e}"
    except Exception as e:
        return f"Erro ao processar o arquivo PDF: {e}"

@tool(name='find_pdf_links', 
      description='Procura especificamente por links de arquivos PDF numa página específica.')
def find_pdf_links(url: str) -> list:
    try:
        target_url = url if url.startswith('http') else f"{BASE_URL}{url}"
        response = requests.get(target_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        pdfs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf') or 'at_download/file' in href:
                pdfs.append({
                    "nome": a.get_text(strip=True) or "Documento PDF",
                    "url": href if href.startswith('http') else f"{BASE_URL}{href}"
                })
        return pdfs
    except Exception:
        return []