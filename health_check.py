# health_check_server.py
import os
from flask import Flask, request

app = Flask("health")

PORT = int(os.getenv("PORT", "3000"))

@app.route("/")
def health_root():
    return "OK", 200

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
