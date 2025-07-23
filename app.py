from flask import Flask, request, jsonify
from flask_cors import CORS
from lotto_utils import load_data, recommend_numbers

app = Flask(__name__)
CORS(app)

@app.route("/api/recommend", methods=["GET"])
def recommend():
    mode = request.args.get("mode", "proportional")
    sets = int(request.args.get("sets", 1))

    data = load_data()
    results = [recommend_numbers(data, proportional=(mode == "proportional")) for _ in range(sets)]

    return jsonify({"recommendations": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)