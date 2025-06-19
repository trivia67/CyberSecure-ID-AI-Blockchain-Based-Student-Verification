import hashlib
import json
from datetime import datetime

blockchain_file = "blockchain.json"

def load_blockchain():
    try:
        with open(blockchain_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return [{
            "block_id": 0,
            "timestamp": str(datetime.utcnow()),
            "student_id": "genesis",
            "status": "init",
            "hash": "0",
            "previous_hash": "0"
        }]

def save_blockchain(chain):
    with open(blockchain_file, "w") as f:
        json.dump(chain, f, indent=4)

def calculate_hash(block):
    block_string = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()

def add_verification_log(student_id, status):
    chain = load_blockchain()
    last_block = chain[-1]

    new_block = {
        "block_id": len(chain),
        "timestamp": str(datetime.utcnow()),
        "student_id": student_id,
        "status": status,
        "previous_hash": last_block["hash"]
    }
    new_block["hash"] = calculate_hash(new_block)
    chain.append(new_block)
    save_blockchain(chain)
    print(f"🧱 Blockchain updated for {student_id} - {status}")
