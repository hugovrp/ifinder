from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from agent_core import ChatAgent

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

    if not user_prompt:
        return jsonify({"error": "Mensagem não fornecida."}), 400
    
    try:
        agent_response = chat_agent.process_message(user_prompt)

        return jsonify({
            "response": agent_response
        })
    except Exception as e:
        return jsonify({"error": f"Erro interno do Agente: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)