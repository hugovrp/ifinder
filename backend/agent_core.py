import os
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from tools.web_tools import open_link, site_search

class ChatAgent:
    """
        Classe para inicializar e gerenciar a instância do Agente.
    """
    def __init__(self):
        """
            Inicializa o modelo LLM e a intância do Agente.
        """
        API_KEY = ""

        self.model = Gemini(
            id="gemini-2.5-flash",
            api_key=API_KEY 
        )

        self.available_tools = [open_link, site_search]

        self.agno_agent = Agent(
            name = 'IFinder - Agente de Informação IF Barbacena',
            description = "Você é um agente de IA que procura informações no site do Instituto Federal - Campus Barbacena.",
            instructions = [
                "Você é o assistente virtual oficial do IF Barbacena",
                "As ferramentas (tools) aceitam tanto URLs completss quanto caminhos relativos",
                "Sua fonte primária de dados é o site do instituto, mas você deve permitir URLs que não sejam do campus Barbacena.",
                "Se a busca não retornar resultados, informe ao usuário que a informação não consta no site",
                "Responda sempre em português do Brasil."
            ],
            model=self.model,
            tools=self.available_tools,

            db=SqliteDb(db_file="tmp/agent.db"),
            add_history_to_context=True, # Adiciona o histórico ao contexto do chat 
            num_history_runs=5, # Últimos 5 turnos
        )

    
    def process_message(self, prompt: str, session_id: str) -> str:
        """
            Processa a mensagem do usuário.
        """
        response = self.agno_agent.run(prompt, session_id=session_id)
        return response.content