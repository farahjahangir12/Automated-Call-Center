from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors= CORS(app,origins='*')

from flask import Flask, request, jsonify
import asyncio
from .main import Assistant
from .router import HospitalRouter

app = Flask(__name__)

# Create event loop if necessary
loop = asyncio.get_event_loop()

# Initialize router and assistant
router = loop.run_until_complete(HospitalRouter.create())
loop.run_until_complete(router.initialize())
assistant = Assistant(router)

@app.route('process_query', methods=['POST'])
def process_query():
    data = request.get_json()

    query = data.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Handle the query asynchronously
    response_text = loop.run_until_complete(assistant.handle_query(query))

    return jsonify({
        "agent": "Hospital Assistant",
        "response": response_text
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
