import os
import uuid
from flask import Flask, request, jsonify
from moviepy import VideoFileClip
import torchaudio
from transformers import AutoModelForCTC, AutoProcessor
import torch

app = Flask(__name__)

# Load base model and processor
BASE_MODEL = "facebook/mms-1b-all"
model = AutoModelForCTC.from_pretrained(BASE_MODEL)
processor = AutoProcessor.from_pretrained(BASE_MODEL)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SEGMENT_DURATION = 10  # seconds

# Supported languages and their adapter names
LANG_ADAPTERS = {
    "eng": "eng",
    "fra": "fra"
}

def split_audio(audio_path, segment_duration=10):
    waveform, sample_rate = torchaudio.load(audio_path)
    total_duration = waveform.shape[1] / sample_rate
    segments = []

    num_segments = int(total_duration // segment_duration) + 1
    for i in range(num_segments):
        start = i * segment_duration
        end = min((i + 1) * segment_duration, total_duration)
        start_frame = int(start * sample_rate)
        end_frame = int(end * sample_rate)
        segment_wave = waveform[:, start_frame:end_frame]

        segment_path = f"{audio_path}_segment_{i}.wav"
        torchaudio.save(segment_path, segment_wave, sample_rate)
        segments.append({
            "start": start,
            "end": end,
            "path": segment_path
        })
    return segments

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Get language
    lang_code = request.form.get('language', 'eng').lower()
    if lang_code not in LANG_ADAPTERS:
        return jsonify({'error': "Invalid language, choose 'eng' or 'fra'"}), 400

    adapter_name = LANG_ADAPTERS[lang_code]

    # Load and activate adapter
    try:
        processor.tokenizer.set_target_lang(adapter_name)
        model.load_adapter(adapter_name)
    except Exception as e:
        return jsonify({"error": f"Failed to load adapter for '{lang_code}': {str(e)}"}), 500

    video_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".mp4")
    audio_path = video_path.replace(".mp4", ".wav")
    file.save(video_path)

    try:
        # Extract audio
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, fps=16000)

        segments = split_audio(audio_path, segment_duration=SEGMENT_DURATION)

        results = []
        for segment in segments:
            speech, sr = torchaudio.load(segment["path"])

            # Convert to mono if stereo
            if speech.shape[0] > 1:
                speech = torch.mean(speech, dim=0, keepdim=True)

            inputs = processor(speech.squeeze(), sampling_rate=sr, return_tensors="pt")

            with torch.no_grad():
                logits = model(**inputs).logits
                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = processor.batch_decode(predicted_ids)[0]

            results.append({
                "start": round(segment["start"], 2),
                "end": round(segment["end"], 2),
                "text": transcription.strip()
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        for f in os.listdir(UPLOAD_FOLDER):
            if f.endswith(".wav") and "segment" in f:
                os.remove(os.path.join(UPLOAD_FOLDER, f))

if __name__ == "__main__":
    app.run(debug=True)
