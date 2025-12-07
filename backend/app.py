from agent_core import ChatAgent

from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
from fastapi.middleware.cors import CORSMiddleware

ifinder_agent = ChatAgent().agno_agent
agent_os = AgentOS(agents=[ifinder_agent], interfaces=[AGUI(agent=ifinder_agent)])
app = agent_os.get_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=True,
    allow_methods=["*"],      
    allow_headers=["*"],
)

if __name__ == "__main__":
    agent_os.serve(app="app:app", host="0.0.0.0", reload=False)