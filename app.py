from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Get the OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"response": "❌ Error: Please enter a message."})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # ✅ Enhanced system prompt for strict and concise replies
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful meditation and exercise assistant. "
                        "Respond ONLY with short, 1-line bullet points. Do NOT go off topic. "
                        "Do not accept or answer inappropriate or unrelated questions."
                    )
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        if "choices" in result and result["choices"]:
            bot_response = result["choices"][0]["message"]["content"]
        else:
            return jsonify({"response": "❌ Error: Invalid API response."})

        return jsonify({"response": bot_response})

    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"❌ Network error: {str(e)}"})

    except Exception as e:
        return jsonify({"response": f"❌ Error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
