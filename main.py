from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

PROMPT_TEMPLATE = (
    "Translate the following text from {source_lang} to {target_lang}:\n\n"
    "Text: {text}\n\n"
    "Remember to return only the translation, explanation or additional information is not required.\n"
    "Translation:"
)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get("text", "").strip()
    source_lang = data.get("source_lang", "").strip()
    target_lang = data.get("target_lang", "").strip()

    if not text or not source_lang or not target_lang:
        return jsonify({"error": "Missing required fields: text, source_lang, target_lang"}), 400

    prompt = PROMPT_TEMPLATE.format(
        source_lang=source_lang,
        target_lang=target_lang,
        text=text
    )

    try:
        # subprocess call to ollama CLI
        result = subprocess.run(
            ["ollama", "run", "gemma3:4b", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            # Return stderr output if error occurs
            return jsonify({"error": result.stderr.strip()}), 500

        translation = result.stdout.strip()
        return jsonify({"translation": translation})

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Ollama call timed out"}), 504

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
