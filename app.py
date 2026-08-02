import os
# Ye sabse zaroori hai bina error ke chalane ke liye (Terms of Service bypass)
os.environ["COQUI_TOS_AGREED"] = "1"

from flask import Flask, render_template, request, send_file
from TTS.api import TTS
import uuid

app = Flask(__name__)

# Folder setup
UPLOAD_FOLDER = 'temp_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AI Model Loading - Ye server start hote hi ek baar load hoga
print("AI Model download aur load ho raha hai... (Sirf pehli baar time lagta hai)")
try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("Model Successfully Loaded! Koi error nahi aaya.")
except Exception as e:
    print(f"Model Load Error: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # File checks
        if 'audio_file' not in request.files:
            return "Error: Koi audio file upload nahi ki!", 400
        
        file = request.files['audio_file']
        text = request.form.get('text')
        language = request.form.get('language', 'hi')
        
        if file.filename == '' or not text:
            return "Error: File aur Text dono zaroori hain!", 400

        # Unique ID taki multiple log ek sath use karein toh files mix na hon
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"in_{unique_id}.wav")
        output_path = os.path.join(UPLOAD_FOLDER, f"out_{unique_id}.wav")
        
        file.save(input_path)

        try:
            # Voice Clone Processing
            tts.tts_to_file(
                text=text, 
                speaker_wav=input_path, 
                language=language, 
                file_path=output_path
            )
            return send_file(output_path, as_attachment=True, download_name="cloned_voice.wav")
            
        except Exception as e:
            return f"Server par Processing Error: {str(e)}", 500
        finally:
            # Server ka space free karne ke liye original file delete kar do
            if os.path.exists(input_path):
                os.remove(input_path)

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
