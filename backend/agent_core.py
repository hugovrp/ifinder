import os
from agno.agent import Agent
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from tools.file_tools import read_pdf
from tools.web_tools import open_link, site_search_simple, site_search, open_link_in_selenium

load_dotenv()

class ChatAgent:
    """
        Classe para inicializar e gerenciar a instância do Agente.
    """
    def __init__(self):
        """
            Inicializa o modelo LLM e a intância do Agente.
        """
        API_KEY = os.getenv("GOOGLE_API_KEY")

        self.model = Gemini(
            id="gemini-2.5-flash",
            api_key=API_KEY 
        )
        self.db = SqliteDb(db_file="tmp/agent.db")
        self.available_tools = [open_link, open_link_in_selenium, site_search_simple, site_search, read_pdf]
        self.agno_agent = Agent(
            name = 'IFinder - Agente de Informação IF Barbacena',
            description = "Você é um agente de IA que procura informações no site do Instituto Federal - Campus Barbacena.",
            instructions = [
                "Você é o assistente virtual oficial do IF Barbacena",
                "Utilize todas as suas tools disponíveis, de acordo com o que lhe é pedido", 
                "Se uma busca retornar um link para um arquivo .pdf, utilize a tool 'read_pdf' com este link para extrair o conteúdo do documento e responder ao usuário.",
                "Sempre tente usar as ferramentas antes de dizer que não sabe",
                "Se site_search_simple não encontrar nada, tente site_search com filtros mais amplos",
                "Se open_link não retornar resultados úteis nada, tente open_link_in_selenium",
                "As ferramentas (tools) aceitam tanto URLs completas quanto caminhos relativos",
                "Sua fonte primária de dados é o site do instituto, mas você deve permitir URLs que não sejam do campus Barbacena.",
                "Se nenhuma ferramenta retornar resultados úteis, só então informe que a informação não foi encontrada",
                "Se a busca não retornar resultados, informe ao usuário que a informação não consta no site",
                "Responda sempre em português do Brasil."
            ],
            model=self.model,
            tools=self.available_tools,

            db=self.db,
            add_history_to_context=True, # Adiciona o histórico ao contexto do chat 
            num_history_runs=5,          # Últimos 5 turnos
        )

    
    def process_message(self, prompt: str, user_id: str, session_id: str) -> str:
        """
            Processa a mensagem do usuário.
        """
        response = self.agno_agent.run(prompt, user_id=user_id, session_id=session_id)
        return response.content