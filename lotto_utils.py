import os
import time
import requests
import pandas as pd
import random

DATA_FILE = "lotto_data.csv"
BASE_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber"

# ----------------------------------
# 🔹 최신 회차 조회
# ----------------------------------
def get_latest_round():
    """9999 회차 요청 실패 시 역순으로 최신 회차 추정"""
    try:
        url = f"{BASE_URL}&drwNo=9999"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return data.get("drwNo")
        # 실패 시 1200부터 역순 탐색
        for round_no in range(1200, 0, -1):
            url = f"{BASE_URL}&drwNo={round_no}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("returnValue") == "success":
                    return round_no
        return None
    except Exception as e:
        print(f"❌ 최신 회차 조회 실패: {e}")
        return None

# ----------------------------------
# 🔹 특정 회차 데이터 가져오기
# ----------------------------------
def get_round(round_no):
    try:
        url = f"{BASE_URL}&drwNo={round_no}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return {
                    "drwNo": data["drwNo"],
                    "drwtNo1": data["drwtNo1"],
                    "drwtNo2": data["drwtNo2"],
                    "drwtNo3": data["drwtNo3"],
                    "drwtNo4": data["drwtNo4"],
                    "drwtNo5": data["drwtNo5"],
                    "drwtNo6": data["drwtNo6"],
                    "bnusNo": data["bnusNo"],
                }
        return None
    except Exception:
        return None

# ----------------------------------
# 🔹 모든 회차 데이터 수집 및 저장
# ----------------------------------
def load_data(limit_rounds=200):
    latest = get_latest_round()
    if not latest:
        print("❌ 최신 회차 조회 실패 - 데이터 로딩 중단")
        return

    print(f"📦 최신 회차: {latest}, 최근 {limit_rounds}회 수집 시작")

    data = []
    for round_no in range(latest, max(latest - limit_rounds, 0), -1):
        round_data = get_round(round_no)
        if round_data:
            data.append(round_data)
            print(f"✅ {round_no}회차 저장 완료")
        time.sleep(0.1)

    if not data:
        print("⚠️ 로드된 데이터 없음 - 중단")
        return

    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    print(f"💾 {len(df)}개 회차 데이터 저장 완료 ({DATA_FILE})")

# ----------------------------------
# 🔹 데이터 불러오기
# ----------------------------------
def load_existing_data():
    if not os.path.exists(DATA_FILE):
        print("⚠️ CSV 파일이 존재하지 않습니다.")
        return None
    try:
        df = pd.read_csv(DATA_FILE)
        required_columns = {"drwtNo1", "drwtNo2", "drwtNo3", "drwtNo4", "drwtNo5", "drwtNo6"}
        if not required_columns.issubset(df.columns):
            print("❌ 필수 컬럼 누락 - 데이터 무효")
            return None
        return df
    except Exception as e:
        print(f"❌ CSV 파일 로드 실패: {e}")
        return None

# ----------------------------------
# 🔹 추천번호 생성 로직
# ----------------------------------
def get_recommendations(mode="proportional", sets=5):
    df = load_existing_data()
    if df is None or df.empty:
        raise ValueError("데이터가 로드되지 않았습니다.")

    numbers = pd.concat([
        df["drwtNo1"], df["drwtNo2"], df["drwtNo3"],
        df["drwtNo4"], df["drwtNo5"], df["drwtNo6"]
    ])
    freq = numbers.value_counts().sort_index()

    all_numbers = list(range(1, 46))
    weights = [freq.get(n, 1) for n in all_numbers]

    results = []
    for _ in range(sets):
        if mode == "proportional":
            picks = random.choices(all_numbers, weights=weights, k=6)
        elif mode == "inverse":
            inverse_weights = [max(weights) - w + 1 for w in weights]
            picks = random.choices(all_numbers, weights=inverse_weights, k=6)
        else:
            picks = random.sample(all_numbers, 6)

        picks = sorted(list(set(picks)))
        while len(picks) < 6:
            picks.append(random.choice(all_numbers))
            picks = sorted(list(set(picks)))
        results.append(picks)

    return results
