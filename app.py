import os
os.environ["PYTHONMALLOC"] = "malloc"
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
import requests
from flask_cors import CORS
import cv2
import numpy as np
import mediapipe as mp
import gc
import threading
from werkzeug.utils import secure_filename

# Flask app setup
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
POSES_FOLDER = 'static/poses'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load .env vars
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# MediaPipe Pose initialization
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=True, model_complexity=1)

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Chat route (uses session pose feedback)
@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"response": "❌ Error: Please enter a message."})

        last_pose_feedback = session.get("last_pose_feedback", "")
        context = f"The user uploaded a posture image. Feedback: {last_pose_feedback}" if last_pose_feedback else ""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful meditation and exercise assistant. "
                        "Reply only in short, one-line bullet points. Strictly stay on-topic."
                    )
                },
                {
                    "role": "user",
                    "content": context + "\n" + user_input if context else user_input
                }
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and result["choices"]:
            return jsonify({"response": result["choices"][0]["message"]["content"]})
        else:
            return jsonify({"response": "❌ Error: Invalid API response."})

    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"❌ Network error: {str(e)}"})
    except Exception as e:
        return jsonify({"response": f"❌ Error: {str(e)}"})

# Pose analysis route


@app.route('/analyze_pose', methods=['POST'])
def analyze_pose():
    try:
        if 'file' not in request.files:
            return jsonify({'result': '❌ No image uploaded.', 'image_url': None})

        file = request.files['file']
        img_array = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'result': '❌ Invalid image file.', 'image_url': None})

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Create Pose instance only once
        with mp_pose.Pose(static_image_mode=True, model_complexity=2) as pose_model:
            user_result = pose_model.process(img_rgb)

            if not user_result.pose_landmarks:
                return jsonify({'result': '⚠️ No pose detected. Try a clearer photo.', 'image_url': None})

            user_landmarks = user_result.pose_landmarks.landmark
            user_coords = np.array([(lm.x, lm.y, lm.z) for lm in user_landmarks]).flatten()

            best_score = float('inf')
            matched_pose = None

            for i in range(1, 13):
                ref_path = f'static/poses/n{i}.jpg'
                ref_img = cv2.imread(ref_path)
                if ref_img is None:
                    continue

                ref_rgb = cv2.cvtColor(ref_img, cv2.COLOR_BGR2RGB)
                ref_result = pose_model.process(ref_rgb)

                if not ref_result.pose_landmarks:
                    continue

                ref_landmarks = ref_result.pose_landmarks.landmark
                ref_coords = np.array([(lm.x, lm.y, lm.z) for lm in ref_landmarks]).flatten()

                score = np.linalg.norm(user_coords - ref_coords)
                if score < best_score:
                    best_score = score
                    matched_pose = f'/static/poses/n{i}.jpg'

        THRESHOLD = 0.1
        if best_score < THRESHOLD:
            feedback = "✅ Your posture looks correct. Keep it up!"
            image_url = None
        else:
            feedback = "❌ Your posture is incorrect. Please follow the reference image below."
            image_url = matched_pose

        # Save feedback in session for context-aware chat
        session["last_pose_feedback"] = feedback

        return jsonify({
            'result': feedback,
            'image_url': image_url
        })

    except Exception as e:
        print("Pose analysis crash:", str(e))
        return jsonify({'result': f"❌ Pose detection failed: {str(e)}", 'image_url': None})

if __name__ == '__main__':
    app.run(debug=True)
