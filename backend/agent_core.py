import os
from agno.agent import Agent
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
            id="gemini-2.0-flash",
            api_key=API_KEY 
        )

        self.available_tools = [open_link, site_search]

        self.agno_agent = Agent(
            name='IFinder - Agente de Informação IF Barbacena',
            instructions=(
                """
                    Você é um agente de IA focado no Campus Barbacena. Use as ferramentas ('open_link' e 'site_search') 
                    para buscar dados no portal antes de responder.
                """
            ),
            model=self.model,
            tools=self.available_tools
        )
    
    def process_message(self, prompt: str) -> str:
        """
            Processa a mensagem do usuário.
        """
        response = self.agno_agent.run(prompt)
        return response.content