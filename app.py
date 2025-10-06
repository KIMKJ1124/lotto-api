import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
from lotto_utils import load_data, get_recommendations

app = Flask(__name__)
CORS(app)

# 전역 상태 플래그
data_loaded = False
data_loading = False

# -----------------------------
# 🔹 데이터 로딩 비동기 스레드
# -----------------------------
def init_data_async():
    global data_loaded, data_loading
    if data_loaded or data_loading:
        return
    data_loading = True
    try:
        print("📦 데이터 초기화 시작...")
        load_data(limit_rounds=200)  # 최근 200회까지만 로드
        data_loaded = True
        print("✅ 데이터 로딩 완료")
    except Exception as e:
        print(f"❌ 데이터 로드 중 오류: {e}")
    finally:
        data_loading = False

# -----------------------------
# 🔹 상태 확인용 엔드포인트
# -----------------------------
@app.route("/status")
def status():
    return jsonify({
        "data_loaded": data_loaded,
        "data_loading": data_loading
    })

# -----------------------------
# 🔹 추천 API
# -----------------------------
@app.route("/api/recommend", methods=["GET"])
def recommend_numbers():
    if not data_loaded:
        return jsonify({
            "status": "loading",
            "message": "서버가 데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요."
        }), 503

    mode = request.args.get("mode", "proportional")
    sets = int(request.args.get("sets", 5))

    try:
        recommendations = get_recommendations(mode=mode, sets=sets)
        return jsonify({
            "status": "success",
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -----------------------------
# 🔹 기본 라우트
# -----------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "🎯 Lotto API is running",
        "endpoints": ["/api/recommend", "/status"]
    })

# -----------------------------
# 🔹 Render 환경 포트 설정
# -----------------------------
if __name__ == "__main__":
    Thread(target=init_data_async).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask server running on port {port}")
    app.run(host="0.0.0.0", port=port)
