import requests
from agno.tools import tool
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager

# Código base do site do Instituto Federal - Campus Barbacena
BASE_URL = 'https://www.ifsudestemg.edu.br'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

@tool(name='get_site_highlights', 
      description='PRIMEIRA OPÇÃO para notícias: Retorna automaticamente as 5 notícias mais recentes do Campus Barbacena sem precisar de parâmetros. Use SEMPRE que o usuário perguntar sobre notícias, novidades, destaques, ou "o que há de novo". NÃO requer busca - acessa direto a página de notícias.')
def get_site_highlights():
    try:
        url = "https://www.ifsudestemg.edu.br/noticias/barbacena"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Procura os itens de notícia (ajustado para a estrutura comum do Plone/Portal Padrão)
        news_items = soup.find_all('h2', class_='tileHeadline')
        
        if not news_items:
            return "Não foi possível encontrar notícias recentes no layout atual da página."

        results = ["Últimas Notícias do Campus Barbacena:"]
        for item in news_items[:5]: # Limite das 5 mais recentes
            title = item.get_text(strip=True)
            link_tag = item.find('a', href=True)
            link = link_tag['href'] if link_tag else "Link não disponível"
            results.append(f"- {title} (Link: {link})")
        
        return "\n".join(results)
    except Exception as e:
        return f"Erro ao aceder às notícias em tempo real: {str(e)}"

@tool(name='get_page_navigation',
      description='Extrai TODOS os links de navegação e menus de uma página específica. Use para: 1) Descobrir quais seções/páginas estão disponíveis em uma área do site, 2) Listar links relacionados a um tema, 3) Explorar menus e submenus. Útil quando você sabe a área mas não o link exato. Requer URL da página como parâmetro.')
def get_page_navigation(url: str) -> str:
    try:
        target_url = url if url.startswith('http') else f"{BASE_URL}{url}"
        response = requests.get(target_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Focar no conteúdo principal e menus, ignorando rodapés pesados
        nav_elements = soup.find_all(['nav', 'div'], {'id': ['content', 'portal-column-one', 'viewlet-above-content']})
        
        links = []
        for area in nav_elements:
            for a in area.find_all('a', href=True):
                texto = a.get_text(strip=True)
                href = a['href']
                if texto and len(texto) > 3:
                    links.append(f"[{texto}]({href})")

        return "\n".join(list(set(links))[:50]) # Retorna os primeiros 50 links únicos
    except Exception as e:
        return f"Erro ao navegar: {str(e)}"

@tool(name='open_link', 
      description='FERRAMENTA PRINCIPAL: Abre qualquer URL e retorna o conteúdo da página formatado + lista completa de links. Use esta ferramenta para: 1) Ler conteúdo de uma página específica quando você tem a URL, 2) Obter detalhes de uma notícia, 3) Acessar páginas institucionais (corpo docente, fale conosco, etc). SEMPRE prefira esta ferramenta quando souber a URL ou tiver recebido uma URL de outra ferramenta.')
def open_link(url: str) -> dict:
    """
        Recupera o conteúdo de uma página web e retorna o texto visível e todos os links encontrados na página.
        A URL pode ser fornecida de forma absoluta ou relativa ao domínio padrão do Campus Barbacena.
        A função é utilizada pelo agente de IA para recuperar informações do site institucional, permitindo 
        que o modelo obtenha dados diretamente das páginas para análise do conteúdo publicado em páginas específicas.

    Args:
        url (str): Endereço da página a ser acessada. Pode ser uma URL completa
                   (iniciando com http/https) ou um caminho relativo ao domínio base.

    Returns:
        dict:
            Em caso de sucesso:
            {
                "text": "<conteúdo textual da página>",
                "links": [
                    { "text": "<texto do link>", "url": "<endereço do link>" },
                    ...
                ]
            }

            Em caso de erro: {"error": "<mensagem de erro>"}
    """
    try:
        # Aceita URL absoluta ou relativa
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

        # Coleta os links
        links = []
        for a in soup.find_all("a"):
            text = a.get_text(" ", strip=True)
            href = a.get("href", "")
            
            if not href:
                continue

            links.append({
                "text": text if text else None,
                "url": href
            })

        # Extrai somente o texto visual
        text = soup.get_text(separator='\n', strip=True)
        if not text:
            return {"error": f"Erro ao acessar conteúdo da URL {url}."}

        return {"text": text, "links": links}
            
    except Exception as e:
        return {"error": f"Erro ao acessar a URL {url}."}

@tool(
    name='open_link_in_selenium',
    description='SEGUNDA ESCOLHA para páginas dinâmicas: Abre URL usando navegador real (Chrome headless ou Firefox headless) para carregar conteúdo JavaScript/AJAX. Use quando: 1) open_link falhou ou retornou conteúdo incompleto, 2) Página usa JavaScript pesado (ex: corpo docente, listas longas), 3) Conteúdo aparece vazio ou cortado. IMPORTANTE: Mais lento que open_link, use apenas quando necessário.')
def open_link_in_selenium(url: str) -> dict:
    """
        Abre uma página web utilizando um navegador real controlado pelo Selenium (Google Chrome ou Firefox em modo headless).
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

    try:
        # Configuração do navegador Chrome, executa-o em modo headless (sem interface gráfica)
        options = Options()
        options.add_argument('--headless=new')

        # Baixa e inicializa o ChromeDriver compatível com o Google Chrome instalado na máquina
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    except Exception:
        options = FirefoxOptions()
        options.add_argument("--headless")

        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options
        )

    # Abre a página da url
    driver.get(full_url)

    # Acessa o DOM atual do navegador (HTML)
    html = driver.page_source

    # Fecha a janela do navegador e finaliza o processo do ChromeDriver
    driver.quit()

    return {'html': html}

""" Teste:
    curl -X POST http://127.0.0.1:5000/chat -H "Content-Type: application/json" -d "{\"prompt\": \"Use a tool site_search_simple com o seguinte parâmetro: query=\\\"refeitório\\\". Mostre o resultado retornado pela tool.\", \"session_id\": \"test_simple_01\"}"
"""
@tool(name='site_search_simple', 
      description='ÚLTIMO RECURSO: Busca básica no mecanismo de busca interno do site (requer texto EXATO para funcionar bem). Use SOMENTE quando: 1) Não existe URL direta conhecida, 2) Outras ferramentas (get_site_highlights, open_link, get_page_navigation) não são aplicáveis, 3) Você realmente não sabe onde procurar. LIMITAÇÃO IMPORTANTE: A busca interna do site é RUIM e DESATUALIZADA - ela requer correspondência exata de texto.')
def site_search_simple(query: str) -> str:
    """
        Busca simples que retorna títulos e links encontrados.
        Args:
            query (str): O termo a ser pesquisado.
    """
    try:
        url = "https://www.ifsudestemg.edu.br/barbacena/@@busca"
        params = {'SearchableText': query}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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

@tool(name='site_search', 
      description='ÚLTIMO RECURSO com filtros: Versão avançada de site_search_simple que permite filtrar por tipo de documento (Notícia, Edital, Evento, Arquivo, etc), data e ordenação. Use SOMENTE quando site_search_simple não encontrar resultados E você precisa filtrar por tipo específico de conteúdo. LIMITAÇÃO CRÍTICA: A busca interna do site é RUIM e requer texto exato - sempre prefira usar URLs diretas e outras ferramentas.')
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
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=15)
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