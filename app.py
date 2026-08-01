from flask import Flask, render_template, request, send_file
import requests
import os
import tempfile

app = Flask(__name__)

# Yahan apni ElevenLabs ki API Key daalein
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY_HERE"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clone', methods=['POST'])
def clone_voice():
    if 'audio' not in request.files or 'text' not in request.form:
        return "Error: Audio file ya text missing hai!", 400

    audio_file = request.files['audio']
    new_text = request.form['text']

    # 1. Temporary file mein audio save karein
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, audio_file.filename)
    audio_file.save(audio_path)

    # 2. ElevenLabs API par Voice Add karne ki request (Instant Voice Cloning)
    add_voice_url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    data = {
        'name': 'Temp Cloned Voice',
        'description': 'User uploaded voice'
    }
    
    files = [
        ('files', (audio_file.filename, open(audio_path, 'rb'), 'audio/mpeg'))
    ]

    print("Uploading voice to API...")
    add_response = requests.post(add_voice_url, headers=headers, data=data, files=files)
    
    if add_response.status_code != 200:
        return f"Error adding voice: {add_response.text}", 400
        
    voice_id = add_response.json()['voice_id']

    # 3. Naye text ke saath audio generate karein
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    tts_payload = {
        "text": new_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    print("Generating new audio...")
    tts_response = requests.post(tts_url, headers=headers, json=tts_payload)

    if tts_response.status_code != 200:
        return f"Error generating audio: {tts_response.text}", 400

    # 4. Generated audio ko save karke user ko bhejna
    output_audio_path = os.path.join(temp_dir, "output.mp3")
    with open(output_audio_path, 'wb') as f:
        f.write(tts_response.content)

    # (Optional) API se temporary voice delete kar dein taaki account limit khatam na ho
    requests.delete(f"https://api.elevenlabs.io/v1/voices/{voice_id}", headers=headers)

    return send_file(output_audio_path, as_attachment=True, download_name="cloned_audio.mp3")

if __name__ == '__main__':
    # Render ke liye port aur host configure karna
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
