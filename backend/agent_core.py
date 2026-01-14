import os
import requests
from agno.agent import Agent
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from datetime import datetime, timedelta
from agno.session import SessionSummaryManager
from tools.pdf_tools import read_pdf, find_pdf_links
from tools.selenium_tools import open_link_in_selenium
from tools.web_tools import open_link, site_search_simple, site_search, get_page_navigation, get_site_highlights

load_dotenv()

class ChatAgent:
    """
        Classe para inicializar e gerenciar a instância do Agente.
    """
    def __init__(self):
        """
            Inicializa o modelo LLM e a intância do Agente.
        """
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        SUMMARIZER_API_KEY = os.getenv("SUMMARIZER_API_KEY")

        self.model = Gemini(
            id="models/gemini-2.5-flash-lite",
            api_key=GOOGLE_API_KEY
        )
        self.db = SqliteDb(db_file="tmp/agent.db")

        main_pages = (
            "URLs DIRETAS PARA ATALHOS IMPORTANTES (USE SEMPRE):\n"
            "- Fale Conosco: https://www.ifsudestemg.edu.br/barbacena/fale-conosco\n"
            "- Corpo Docente: https://www.ifsudestemg.edu.br/barbacena/institucional/corpo-docente\n"
            "- Página Inicial: https://www.ifsudestemg.edu.br/barbacena\n"
            "- Notícias: https://www.ifsudestemg.edu.br/noticias/barbacena\n"
            "- Calendário: https://www.ifsudestemg.edu.br/documentos-institucionais/unidades/barbacena/diretorias-sistemicas/ensino/calendario-academico\n"
            "- Assistência Estudantil: https://www.ifsudestemg.edu.br/barbacena/institucional/ensino/apoio-ao-discente/assistencia-estudantil\n"
            "- Mapa do Site: https://www.ifsudestemg.edu.br/barbacena/mapadosite\n"
        )
        
        self.available_tools = [open_link, open_link_in_selenium, site_search_simple, site_search, 
                                read_pdf, find_pdf_links, get_page_navigation,  get_site_highlights]

        self.agno_agent = Agent(
            name = 'IFinder - Agente de Informação IF Barbacena',
            description = "Você é um agente de IA que busca informações no site do Instituto Federal - Campus Barbacena.",
            instructions = [
                f"Você é o IFinder, assistente virtual do IF Sudeste MG - Campus Barbacena. Hoje é {datetime.now().strftime('%d/%m/%Y')}.",
                main_pages,

                "=== HIERARQUIA DE FERRAMENTAS (SIGA ESTA ORDEM SEMPRE) ===",
                "",
                "1. PRIMEIRA ESCOLHA - Ferramentas diretas (use quando aplicável):",
                "   • get_site_highlights: Para notícias/novidades (não precisa parâmetros)",
                "   • open_link: Quando tiver URL específica (páginas institucionais, links conhecidos)",
                "   • get_page_navigation: Para descobrir links/seções disponíveis em uma página",
                "",
                "2. SEGUNDA ESCOLHA - Conteúdo dinâmico:",
                "   • open_link_in_selenium: Se open_link falhar ou conteúdo carregar via JavaScript",
                "",
                "3. ARQUIVOS PDF (Exclusivo):",
                "   • read_pdf: ÚNICA forma de ler arquivos PDF. Use se URL terminar em .pdf",
                "   • find_pdf_links: Para encontrar PDFs em uma página",
                "",
                "4. ÚLTIMO RECURSO - Busca (só se NÃO souber onde procurar):",
                "   • site_search_simple ou site_search: Quando nenhuma das acima for aplicável",
                "   • AVISO: Busca interna do site é RUIM, DESATUALIZADA e requer texto EXATO",
                "",
                "REGRA DE OURO: Sempre que souber ou descobrir uma URL, use open_link. NUNCA busque se tiver URL!",
                "",

                "- COMPORTAMENTO CRÍTICO:",
                "- Se uma ferramenta falhar, tente a próxima da MESMA CATEGORIA antes de descer de nível.",
                "- Só use ferramentas de busca após TODAS as outras opções falharem.",
                "- Se o conteúdo de uma página parecer cortado ou incompleto, OBRIGATORIAMENTE use 'open_link_in_selenium'.",
                "- Para listas longas (como Corpo Docente), saiba que o texto pode exceder o limite; use Selenium se não encontrar o que busca de primeira.",

                "- ESTRATÉGIA POR CATEGORIA:",
                
                "PROFESSORES E DOCENTES:",
                "- Vá DIRETO para: 'https://www.ifsudestemg.edu.br/barbacena/institucional/corpo-docente'.",
                "- Se não encontrar o nome (ex: Herlon) com 'open_link', use 'open_link_in_selenium' imediatamente, pois a página é longa e pode carregar via JS.",

                "NOTÍCIAS E DESTAQUES:",
                "- Use a tool 'get_site_highlights'. Se falhar, use 'open_link_in_selenium' na página de notícias.",
                "- Ou acesse 'https://www.ifsudestemg.edu.br/noticias/barbacena' para ler detalhes.",

                "CARDÁPIO E REFEITÓRIO:",
                "- O cardápio geralmente é uma NOTÍCIA recente. Verifique 'get_site_highlights' ou a página de notícias primeiro.",
                "- Alternativa: Navegue em 'https://www.ifsudestemg.edu.br/barbacena/estudante' usando 'get_page_navigation' para achar a seção de Assistência Estudantil/Refeitório.",
                "- Se achar um link de PDF, use 'read_pdf'. Verifique se a DATA no PDF condiz com a semana atual.",

                "CALENDÁRIO ACADÊMICO:",
                "- Tente navegar via 'https://www.ifsudestemg.edu.br/documentos-institucionais/unidades/barbacena/diretorias-sistemicas/ensino/calendario-academico'.",
                "- Procure o PDF do ano letivo atual (ex: 2024 ou 2025) usando 'find_pdf_links' e 'read_pdf'.",

                "CONTATOS E COORDENAÇÕES:",
                "- Use 'get_page_navigation' na Home ou na página 'Fale Conosco'.",
                "- Procure por menus como 'Ensino' -> 'Cursos' para achar coordenações específicas.",

                "- REGRAS DE EXECUÇÃO:",
                "- Se 'open_link' retornar um erro ou texto vazio, use 'open_link_in_selenium'.",
                "- Se a informação for um documento (Cardápio, Edital, Calendário), você PRECISA ler o conteúdo do PDF com 'read_pdf' antes de responder.",
                "- No site do instituto, arquivos podem ser organizados por pastas (ex: Calendario 2025/calendario.pdf). Portanto quando for necessario encontrar um pdf, navegue pelas pastas (links) ate que seja encontrado",
                "- As ferramentas aceitam URLs relativas (ex: /barbacena/cursos) ou completas.",
                "- Responda em pt-BR, de forma prestativa, clara e sempre citando a fonte (o link) da informação encontrada."
            ],
            model=self.model,
            tools=self.available_tools,

            db=self.db,
            add_history_to_context=True, # Adiciona o histórico ao contexto do chat 
            num_history_runs=5,          # Últimos 5 turnos

            enable_session_summaries=True, # Permite criação de um resumo do chat
            session_summary_manager = SessionSummaryManager(
                model=Gemini(
                    id="models/gemini-2.5-flash-lite",
                    api_key=SUMMARIZER_API_KEY
                ), 
                session_summary_prompt= """
                Gere um título curto para ser exibido no histórico do usuário.

                Estilo: Use frases nominais curtas (ex: 'Planejamento de Viagem', 'Erro no Python', 'Receita de Bolo'). Evite frases completas ou verbos narrativos como 'Usuário pede...', 'Assistente fala...'.   
                Tamanho: De 3 a 6 palavras.
                Objetivo: O título deve resumir o tópico principal ou a intenção do usuário.
                """
            ),
            add_session_summary_to_context=False,
            debug_mode=True,
            debug_level=2
        )

    
    def process_message(self, prompt: str, user_id: str, session_id: str) -> str:
        """
            Processa a mensagem do usuário.
        """
        response = self.agno_agent.run(prompt, user_id=user_id, session_id=session_id)
        return response.content