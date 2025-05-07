from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import tempfile
import os
from pydub import AudioSegment
from router import HospitalRouter
from livekit.plugins import groq
import base64

app = Flask(__name__)
CORS(app)

# Initialize router at startup - we'll use the same router as in main.py
router = None
stt_engine = None

@app.before_first_request
async def initialize():
    global router, stt_engine
    
    # Initialize the router
    router = await HospitalRouter.create()
    await router.initialize()
    
    # Initialize the STT engine - same as in main.py
    stt_engine = groq.STT(
        model="whisper-large-v3-turbo",
        language="en",
    )

# Helper function to run async code from Flask
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    try:
        # Check if we have audio file or base64 audio
        if 'audio' in request.files:
            # Save the uploaded audio file
            audio_file = request.files['audio']
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                audio_file.save(tmp.name)
                temp_file_path = tmp.name
        elif 'audio_base64' in request.json:
            # Decode base64 audio
            audio_base64 = request.json['audio_base64']
            audio_data = base64.b64decode(audio_base64.split(',')[1] if ',' in audio_base64 else audio_base64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_data)
                temp_file_path = tmp.name
        else:
            return jsonify({'error': 'No audio data provided'}), 400

        # Convert to wav if needed
        audio_segment = AudioSegment.from_file(temp_file_path)
        wav_path = temp_file_path.replace(".webm", ".wav")
        audio_segment.export(wav_path, format="wav")
        
        # Use the same STT engine as main.py
        transcription = run_async(stt_engine.transcribe_file(wav_path))
        
        # Get session ID if provided
        session_id = request.args.get('session_id') or request.json.get('session_id')
        
        # Process with the same router as main.py
        response_data = run_async(router.process_query(transcription, session_id))
        
        # Clean up temporary files
        os.unlink(temp_file_path)
        os.unlink(wav_path)
        
        # Prepare response
        result = {
            "transcription": transcription,
            "response": response_data.get("response", "Sorry, I couldn't process your request."),
            "agent_type": response_data.get("agent_type", "RAG"),
        }
        
        # Include session_id in response if available
        if 'session_id' in response_data:
            result["session_id"] = response_data["session_id"]
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-text', methods=['POST'])
def process_text():
    try:
        # Get text query from request
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text_query = data['text']
        session_id = data.get('session_id')
        
        # Process with the same router as main.py
        response_data = run_async(router.process_query(text_query, session_id))
        
        # Prepare response
        result = {
            "response": response_data.get("response", "Sorry, I couldn't process your request."),
            "agent_type": response_data.get("agent_type", "RAG"),
        }
        
        # Include session_id in response if available
        if 'session_id' in response_data:
            result["session_id"] = response_data["session_id"]
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)