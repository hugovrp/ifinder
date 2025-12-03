import requests
from agno.tools import tool
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BASE_URL = 'https://www.ifsudestemg.edu.br'

# Funções que o Agente usará. 

''' 
    Usa o decorator @Tool para transformar uma função Python comum em uma ferramenta 
    formal que o LLM consegue entender e usar.
'''

@tool(name='open_link', 
      description='Abre um URL e retorna o texto principal da página. Útil para ler o conteúdo de uma notícia ou página específica.')
def open_link(url: str) -> str:
    '''
    Abre uma página web e retorna o conteúdo textual limpo, removendo HTML, scripts e estilos. 
    A URL pode ser fornecida de forma absoluta ou relativa ao domínio padrão do Campus Barbacena.
    A função é utilizada pelo agente de IA para recuperar informações do site institucional, 
    permitindo que o modelo obtenha dados diretamente das páginas.]

    Args:
        url (str): A URL da página a ser acessada. Pode ser:

    Returns:
        str: texto extraído da página, com no máximo 12.000 caracteres ou uma mensagem de erro.
    '''
    try:
        # Aceita URL completo ou relativo
        if url.startswith("http://") or url.startswith("http"):
            full_url = url
        else:
            full_url = f"{BASE_URL.rstrip('/')}/{url.lstrip('/')}"
        
        response = requests.get(full_url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts e CSS
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Extrai somente o texto visual
        text = soup.get_text(separator='\n', strip=True)
        if not text:
            return {"error": f"Erro ao acessar conteúdo da URL {url}."}
        
        text = text[:12000]  # Tamanho máximo seguro
        return text 
    
    except Exception as e: 
        return {"error": f"Erro ao acessar a URL {url}."}

""" Teste:
    curl -X POST http://127.0.0.1:5000/chat -H "Content-Type: application/json" -d "{\"prompt\": \"Use a tool site_search_simple com o seguinte parâmetro: query=\\\"refeitório\\\". Mostre o resultado retornado pela tool.\", \"session_id\": \"test_simple_01\"}"
"""
@tool(name='site_search_simple', 
      description='Realiza uma busca simples por um termo no site do Campus Barbacena.')
def site_search_simple(query: str) -> str:
    """
        Busca simples que retorna títulos e links encontrados.
        Args:
            query (str): O termo a ser pesquisado.
    """
    try:
        url = "https://www.ifsudestemg.edu.br/barbacena/@@busca"
        params = {'SearchableText': query}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
    
        # Pega os resultados
        for dt in soup.select('dl.searchResults dt'):
            # Para cada resultado, extrai o link para obter o título e a URL
            a_tag = dt.find('a')
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag['href']
                results.append(f"- {title}: {link}")
                
        if not results:
            return "Nenhum resultado encontrado."
            
        return "\n".join(results[:10]) # Limita a 10 resultados para não estourar contexto
    except Exception as e:
        return f"Erro na busca: {str(e)}"

""" Teste
    curl -X POST http://127.0.0.1:5000/chat -H "Content-Type: application/json" -d "{\"prompt\": \"Use a tool site_search com os seguintes parâmetros: query=\\\"servidores\\\", item_types=[\\\"pagina\\\"], date_range=\\\"Sempre\\\" e sort_by=\\\"alfabetica\\\". Mostre o resultado retornado pela tool.\",
 \"session_id\": \"test_session_01\"}"
"""
@tool(name='site_search', 
      description='Realiza uma busca avançada no site do IF Barbacena com filtros de tipo, data e ordenação.')
def site_search(query: str, item_types: list[str] = None, date_range: str = None, sort_by: str = None) -> str:
    """
        Realiza busca com filtros.
        Args:
            query (str): Termo de busca.
            item_types (list[str]): Lista de tipos: ['Página', 'Evento', 'Arquivo', 'Notícia', 'Edital', 'Licitação'].
            date_range (str): Filtro de data: 'Ontem', 'Última Semana', 'Último Mês', 'Sempre'.
            sort_by (str): Ordenação: 'Relevância', 'Data (Mais Recente)', 'Alfabética'.
    """
    base_url = "https://www.ifsudestemg.edu.br/barbacena/@@busca"
    
    # Mapeamento de Tipos (Tradução amigável do sistema Plone usado pelo site do IF)
    type_map = {
        'Página': 'Document',
        'Evento': 'Event',
        'Arquivo': 'File',
        'Pasta': 'Folder',
        'Link': 'Link',
        'Ato de Pessoal': 'ato-de-pessoal',
        'Notícia': 'collective.nitf.content',
        'Contrato': 'contrato',
        'Convocação': 'convocacao',
        'Edital': 'edital',
        'Licitação': 'licitacao',
        'Oportunidade': 'oportunidade',
        'Multimídia': 'sc.embedder'
    }
    
    # Lista de tuplas para ser possível enviar múltiplos valores ao request.
    params = [('SearchableText', query)]

    # Adiciona filtros de tipo (portal_type:list)
    if item_types:
        for item in item_types:
            # Busca insensível a maiúsculas/minúsculas
            mapped_val = next((v for k, v in type_map.items() if k.lower() == item.lower()), None)
            if mapped_val:
                params.append(('portal_type:list', mapped_val))

    if date_range and date_range.lower() != 'sempre':
        today = datetime.now()
        start_date = None
        
        dr_lower = date_range.lower()
        if 'ontem' in dr_lower:
            start_date = today - timedelta(days=1)
        elif 'semana' in dr_lower:
            start_date = today - timedelta(weeks=1)
        elif 'mês' in dr_lower or 'mes' in dr_lower:
            start_date = today - timedelta(days=30)
            
        if start_date:
            date_str = start_date.strftime('%Y/%m/%d')
            # Parâmetros Plone
            params.append(('created.query:record:list:date', date_str))
            params.append(('created.range:record', 'min'))

    # Tradução de termos amigáveis para os campos internos do Plone
    if sort_by:
        sb_lower = sort_by.lower()
        if 'data' in sb_lower or 'recente' in sb_lower:
            params.append(('sort_on', 'Date')) 
        elif 'alfabética' in sb_lower or 'alfabetica' in sb_lower:
            params.append(('sort_on', 'sortable_title'))
        elif 'relevância' in sb_lower:
            params.append(('sort_on', 'relevance'))
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
    
        results = []
        search_results_container = soup.select('dl.searchResults dt')
        
        count_text = soup.select_one('#search-results-number')
        total = count_text.get_text(strip=True) if count_text else len(search_results_container)
        
        header = f"Encontrados {total} itens para '{query}' (Mostrando top 10):"
        results.append(header)

        # Pega os resultados
        for dt in search_results_container[:10]:
            # Para cada resultado, extrai o link para obter o título e a URL
            a_tag = dt.find('a')
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag['href']

                # Tenta pegar a descrição 
                dd = dt.find_next_sibling('dd')
                desc = dd.get_text(strip=True)[:150] + "..." if dd and dd.get_text(strip=True) else ""
                
                entry = f"\n- Título: {title}\n  Link: {link}"
                if desc:
                    entry += f"\n  Resumo: {desc}"
                results.append(entry)

        if len(results) == 1: 
            return "Nenhum resultado encontrado com os filtros selecionados."
        return "\n".join(results)

    except Exception as e:
        return f"Erro ao realizar a busca avançada: {str(e)}"