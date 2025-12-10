import os
from agno.agent import Agent
from agno.session import SessionSummaryManager
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from dotenv import load_dotenv
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
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        SUMMARIZER_API_KEY = os.getenv("SUMMARIZER_API_KEY")

        self.model = Gemini(
            id="gemini-2.5-flash",
            api_key=GOOGLE_API_KEY 
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

            enable_session_summaries=True, # Permite criação de um resumo do chat
            session_summary_manager = SessionSummaryManager(
                model=Gemini(
                    id="gemini-2.0-flash",
                    api_key=SUMMARIZER_API_KEY 
                ), 
                session_summary_prompt= """
                Gere um título curto para ser exibido no histórico do usuário.

                Estilo: Use frases nominais curtas (ex: 'Planejamento de Viagem', 'Erro no Python', 'Receita de Bolo'). Evite frases completas ou verbos narrativos como 'Usuário pede...', 'Assistente fala...'.   
                Tamanho: De 3 a 6 palavras.
                Objetivo: O título deve resumir o tópico principal ou a intenção do usuário.
                """
            ),
            add_session_summary_to_context=False
        )

    
    def process_message(self, prompt: str, user_id: str, session_id: str) -> str:
        """
            Processa a mensagem do usuário.
        """
        response = self.agno_agent.run(prompt, user_id=user_id, session_id=session_id)
        return response.content
    
    
    def generate_descriptive_text(self, conversation_history: list) -> str:
        """
            Gera um título curto e descritivo para a conversa com base no histórico recente.

            Esta função formata as últimas mensagens da sessão e utiliza um agente auxiliar (summarizer) para criar 
            um tópico conciso em Português do Brasil, ideal para exibição em interfaces de lista de chats.

            Args:
                conversation_history (list): Lista de dicionários contendo o histórico das mensagens.

            Returns:
                str: O título gerado (aprox. 3 a 6 palavras). 
        """
        if not conversation_history:
            return "Nova Conversa"
        
        # Formata o histórico para o prompt
        history_text = ""
        for msg in conversation_history[-6:]: # Limita as últimas mensagens para economizar tokens
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            # Trunca mensagens muito longas para não confundir o sumarizador
            if len(content) > 500:
                content = content[:500] + "..."
            history_text += f"{role}: {content}\n"

        # Agente temporário apenas para a sumarização
        summarizer_agent = Agent(
            model=self.model,
            description="Você é um assitente especializado em resumir conversas.",
            instructions=[
                "Analise o histórico da conversa fornecido.",
                "Gere um título curto (máximo de 4 a 6 palavras) que descreva o tópico principal.",
                "O título deve estar em Português do Brasil.",
                "Não use aspas, não use ponto final e não seja genérico.",
                "Se a conversa for apenas saudações, retorn 'Nova Conversa'.",
                "Retorne APENAS o texto do título."
            ],
            markdown=False # Retorna texto puro
        )
        try:
            response = summarizer_agent.run(f"Gere um título para:\n{history_text}")
            return response.content
        except Exception as e:
            print(f"Erro ao gerar título: {e}")
            return "Conversa Salva"