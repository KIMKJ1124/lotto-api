# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from lotto_utils import load_data, recommend_numbers, ai_recommend

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "✅ Flask 앱이 작동 중입니다!"

@app.route("/api/recommend", methods=["GET"])
def recommend():
    mode = request.args.get("mode", "proportional")
    sets = int(request.args.get("sets", 1))

    if mode == "ai":
        result = ai_recommend(sets)
    else:
        data = load_data()
        proportional = True if mode == "proportional" else False
        result = [recommend_numbers(data, proportional) for _ in range(sets)]

    return jsonify({"recommendations": result})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)