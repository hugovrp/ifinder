from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from agent_core import ChatAgent
from agno.db.base import SessionType
import uuid

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

chat_agent = ChatAgent()

@app.route('/', methods=['GET'])
def home():
    return send_file('../frontend/index.html')

@app.route('/chat', methods=['POST'])
def handle_chat():
    
    data = request.get_json()
    user_prompt = data.get('prompt')
    session_id = data.get("session_id")
    user_id = data.get("user_id")

    if not user_prompt:
        return jsonify({"error": "Mensagem não fornecida."}), 400
    
    if not session_id or not user_id:
        return jsonify({"error": "ID de usuário e/ou sessão não fornecido."}), 400
    
    try:
        agent_response = chat_agent.process_message(user_prompt, user_id, session_id)

        return jsonify({
            "response": agent_response
        })
    
    except Exception as e:
        return jsonify({"error": f"Erro interno do Agente: {str(e)}"}), 500

@app.route('/auth/generate', methods=['GET'])
def generate_user_id():
    """ Gera um UUID novo para um usuário.
    """
    user_id = str(uuid.uuid4())
    return jsonify({ "user_id": user_id }), 201

@app.route('/sessions/generate', methods=['POST'])
def generate_session_id():
    """ Gera um novo UUID de sessão para um usuário.
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "ID de usuário não fornecido."}), 400

    session_id = str(uuid.uuid4())
    return jsonify({ "session_id": session_id }), 201

@app.route('/sessions/getall', methods=['POST'])
def get_all_conversations():
    """ Obtem todas as conversas entre o agente e um usuário.
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "ID de usuário não fornecido."}), 400

    chats = []

    sessions = chat_agent.db.get_sessions(
        user_id=user_id,
        session_type=SessionType.AGENT
    )

    for session in sessions:
        messages = chat_agent.agno_agent.get_chat_history(session_id=session.session_id)
        messages_list = [ {"role": m.role, "content": m.content} for m in messages ]
        chats.append({
            "summary": session.summary.summary if session.summary else None,
            "messages": messages_list,
        })

    return jsonify({ "chats": chats }), 200

@app.route('/sessions/get', methods=['POST'])
def get_session_conversation():
    """ Obtem a conversa entre o agente e o usuário em uma sessão específica
    
        OBS: A Sessão tem ID único, ou seja, se diferentes usuários tem o mesmo ID
        de sessão, essa sessão é a mesma para os dois.
    """
    data = request.get_json()
    session_id = data.get("session_id")
    user_id = data.get("user_id")

    if not session_id or not user_id:
        return jsonify({"error": "ID de usuário e/ou sessão não fornecido."}), 400

    messages = chat_agent.agno_agent.get_chat_history(session_id=session_id)
    messages_list = [ {"role": m.role, "content": m.content} for m in messages ]
    
    summary = chat_agent.agno_agent.get_session_summary(session_id=session_id)

    return jsonify({ "summary": summary.summary if summary else None,  "messages": messages_list }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)