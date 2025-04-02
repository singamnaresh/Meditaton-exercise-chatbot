# app.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import generativeai as genai

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    # Your logic here
    return jsonify({"message": "Meditation tip: Focus on your breath."})

if __name__ == '__main__':
    app.run(debug=True)
