from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import os
import pickle
import hashlib
from dotenv import load_dotenv
from pymongo import MongoClient
from blockchain import add_verification_log  # Ensure this exists or mock it

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["cybersecure_verification"]
students = db["students"]

# Directory with encoded face .pkl files
DATA_DIR = os.getenv("DATA_DIR", "../Data/faces")

# Encode hash for comparison integrity
def hash_encoding(encoding):
    return hashlib.sha256(np.array(encoding).tobytes()).hexdigest()

@app.route("/verify_face", methods=["POST"])
def verify_face():
    student_id = request.form.get("student_id", "").strip()
    image = request.files.get("image")

    print("🔍 Looking up student ID:", repr(student_id))

    if not student_id or not image:
        return jsonify({"status": "error", "msg": "Missing student_id or image"}), 400

    # Check if face encoding file exists
    file_path = os.path.join(DATA_DIR, f"{student_id}.pkl")
    if not os.path.exists(file_path):
        return jsonify({"status": "fail", "msg": f"No encoding file for ID {student_id}"}), 404

    # Load encoding and hash
    with open(file_path, "rb") as f:
        data = pickle.load(f)
        known_encoding = np.array(data["encoding"])
        known_hash = data["hash"]

    # Load uploaded image
    img_np = face_recognition.load_image_file(image)
    encodings = face_recognition.face_encodings(img_np)

    if len(encodings) != 1:
        return jsonify({"status": "fail", "msg": "Exactly one face must be present"}), 400

    new_encoding = encodings[0]
    new_hash = hash_encoding(new_encoding)

    #if new_hash != known_hash:
     #   return jsonify({"status": "fail", "msg": "Hash mismatch"}), 403

    # Match face
    match = face_recognition.compare_faces([known_encoding], new_encoding)[0]

    if match:
        student_data = students.find_one({"student_id": student_id})
        if not student_data:
            return jsonify({
                "status": "fail",
                "msg": f"No student record found for ID {student_id}."
            }), 404

        # Optional: Log to blockchain
        add_verification_log(student_id, "success")

        return jsonify({
            "status": "success",
            "name": student_data.get("name"),
            "rollno": student_data.get("roll"),
            "email": student_data.get("email"),
            "student_id": student_id
        }), 200

    else:
        add_verification_log(student_id, "fail")
        return jsonify({"status": "fail", "msg": "Face mismatch"}), 401

if __name__ == "__main__":
    app.run(debug=True)
