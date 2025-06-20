from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import os
import pickle
import hashlib
from dotenv import load_dotenv
from pymongo import MongoClient
from blockchain import add_verification_log  # Make sure this works
import datetime

# Load env variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["cybersecure_verification"]
students = db["students"]
blockchain_logs = db["blockchain"]

# Path to face encodings
DATA_DIR = os.getenv("DATA_DIR", "../Data/faces")

def hash_encoding(encoding):
    return hashlib.sha256(np.array(encoding).tobytes()).hexdigest()

@app.route("/verify_face", methods=["POST"])
def verify_face():
    student_id = request.form.get("student_id", "").strip()
    image = request.files.get("image")

    print("🔍 Looking up student ID:", repr(student_id))

    if not student_id or not image:
        return jsonify({"status": "error", "msg": "Missing student_id or image"}), 400

    file_path = os.path.join(DATA_DIR, f"{student_id}.pkl")
    if not os.path.exists(file_path):
        return jsonify({"status": "fail", "msg": f"No encoding file for ID {student_id}"}), 404

    with open(file_path, "rb") as f:
        data = pickle.load(f)
        known_encoding = np.array(data["encoding"])
        known_hash = data["hash"]

    img_np = face_recognition.load_image_file(image)
    encodings = face_recognition.face_encodings(img_np)

    if len(encodings) != 1:
        return jsonify({"status": "fail", "msg": "Exactly one face must be present"}), 400

    new_encoding = encodings[0]
    new_hash = hash_encoding(new_encoding)

    # Skip hash check for now if needed
    # if new_hash != known_hash:
    #     return jsonify({"status": "fail", "msg": "Hash mismatch"}), 403

    match = face_recognition.compare_faces([known_encoding], new_encoding)[0]

    if match:
        student_data = students.find_one({"student_id": student_id})
        if not student_data:
            return jsonify({
                "status": "fail",
                "msg": f"No student record found for ID {student_id}."
            }), 404

        # ✅ Log entry to Mongo blockchain collection
        log_entry = {
            "student_id": student_id,
            "status": "success",
            "timestamp": datetime.datetime.utcnow()
        }
        blockchain_logs.insert_one(log_entry)
        add_verification_log(student_id, "success")  # Optional

        return jsonify({
            "status": "success",
            "name": student_data.get("name"),
            "rollno": student_data.get("roll"),
            "email": student_data.get("email"),
            "student_id": student_id
        }), 200

    else:
        blockchain_logs.insert_one({
            "student_id": student_id,
            "status": "fail",
            "timestamp": datetime.datetime.utcnow()
        })
        add_verification_log(student_id, "fail")
        return jsonify({"status": "fail", "msg": "Face mismatch"}), 401

# ✅ Add this endpoint for frontend dashboard (output.html)
@app.route("/logs", methods=["GET"])
def get_logs():
    logs = []
    for entry in blockchain_logs.find({}, {"_id": 0}):
        student = students.find_one({"student_id": entry["student_id"]}, {"_id": 0})
        logs.append({
            "student_id": entry["student_id"],
            "timestamp": entry["timestamp"],
            "status": entry["status"],
            "name": student.get("name") if student else "",
            "rollno": student.get("roll") if student else ""
        })
    return jsonify({"logs": logs})

if __name__ == "__main__":
    app.run(debug=True)
