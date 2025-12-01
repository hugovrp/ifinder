from agno.agent import Tool

# Funções que o Agente usará. 

""" 
    Usa o decorator @Tool para transformar uma função Python comum em uma ferramenta 
    formal que o LLM consegue entender e usar.
"""

@Tool(name="open_link", description="Abre um URL e retorna o texto principal da página. Útil para ler o conteúdo de uma notícia ou página específica.")
def open_link(url: str) -> str:
    return ""

@Tool(name="site_search", description="Realiza uma busca por um termo específico no site do Campus Barbacena. Retorna uma lista de títulos e URLs.")
def site_search(query: str) -> str:
    return ""