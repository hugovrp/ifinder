from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from agent_core import ChatAgent
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

    if not user_prompt:
        return jsonify({"error": "Mensagem não fornecida."}), 400
    elif not session_id:
        return jsonify({"error": "ID de sessão não fornecido."}), 400
    
    try:
        agent_response = chat_agent.process_message(user_prompt, session_id)

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
    """ Gera um ID de sessão usando um novo UUID e o ID de um usuário.
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "ID de usuário não fornecido."}), 400

    session_id = str(uuid.uuid4())
    return jsonify({ "session_id": f"{user_id}---{session_id}" }), 201

@app.route('/sessions/get', methods=['POST'])
def get_session_conversation():
    """ Obtem a conversa entre o agente e o usuário em uma sessão específica
    """
    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "ID de sessão não fornecido."}), 400

    messages = chat_agent.agno_agent.get_chat_history(session_id=session_id)
    messages_list = [ {"role": m.role, "content": m.content} for m in messages ]
    
    return jsonify({ "chat": messages_list }), 200

@app.route('/sessions/title', methods=['POST'])
def generate_session_title():
    """
        Gera um título descritivo para uma sessão específica baseado no histórico atual.
    """
    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "ID de sessão não fornecido."}), 400
    
    try:
        try:
            messages = chat_agent.agno_agent.get_chat_history(session_id=session_id)
        except Exception: # Assume que é uma nova conversa
            return jsonify({"title": "Nova Conversa"}), 200

        messages_list = [{"role": m.role, "content": m.content} for m in messages]

        if not messages_list:
            return jsonify({"title": "Nova Conversa"}), 200
        
        title = chat_agent.generate_descriptive_text(messages_list)

        return jsonify({"title": title}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar título: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)