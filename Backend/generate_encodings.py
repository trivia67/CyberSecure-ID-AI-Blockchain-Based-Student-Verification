import face_recognition
import os
import pickle
import numpy as np
import hashlib



def hash_encoding(encoding):
    return hashlib.sha256(np.array(encoding).tobytes()).hexdigest()

faces_folder = "../data/faces"
os.makedirs(faces_folder, exist_ok=True)

for filename in os.listdir(faces_folder):
    if filename.endswith(".jpg"):
        path = os.path.join(faces_folder, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) != 1:
            print(f"❌ {filename} skipped — must contain exactly 1 face.")
            continue

        encoding = encodings[0]
        hashed = hash_encoding(encoding)
        save_name = os.path.splitext(filename)[0]

        with open(os.path.join(faces_folder, f"{save_name}.pkl"), "wb") as f:
            pickle.dump({"encoding": encoding, "hash": hashed}, f)

        print(f"✅ {save_name}.pkl created.")
