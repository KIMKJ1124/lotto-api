import pandas as pd
import requests
import random
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

XLSX_FILE = "lotto_data.xlsx"

# 🔍 최신 회차 번호 가져오기
def get_latest_round():
    url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=9999"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("drwNo", 0)
    return 0

# ✅ JSON API 기반 회차별 당첨번호 수집
def fetch_lotto_data(start=1, end=None):
    if end is None:
        end = get_latest_round()
    url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber"
    all_rounds = []
    for round_no in range(start, end + 1):
        print(f"{round_no}회차 수집 중...")
        response = requests.get(url, params={"drwNo": round_no})
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                numbers = [
                    data["drwtNo1"], data["drwtNo2"], data["drwtNo3"],
                    data["drwtNo4"], data["drwtNo5"], data["drwtNo6"]
                ]
                all_rounds.append(numbers)
    print("✅ 모든 회차 수집 완료")
    return all_rounds

# 💾 엑셀 저장
def save_lotto_data(data):
    df = pd.DataFrame(data)
    df.to_excel(XLSX_FILE, index=False, engine="openpyxl")

# 📥 데이터 로딩 (없으면 자동 수집)
def load_data():
    if not os.path.exists(XLSX_FILE):
        print("데이터 파일이 없어 웹에서 수집합니다...")
        data = fetch_lotto_data()
        save_lotto_data(data)
    else:
        # 최신 회차 갱신 확인
        df = pd.read_excel(XLSX_FILE, engine="openpyxl")
        latest_local = len(df)
        latest_online = get_latest_round()
        if latest_local < latest_online:
            print(f"📈 새로운 회차 발견! {latest_local + 1} ~ {latest_online}회차 추가 수집 중...")
            new_data = fetch_lotto_data(start=latest_local + 1, end=latest_online)
            if new_data:
                df_new = pd.DataFrame(new_data)
                df = pd.concat([df, df_new], ignore_index=True)
                save_lotto_data(df.values.tolist())
    return pd.read_excel(XLSX_FILE, engine="openpyxl")

# 📊 번호 빈도 계산
def calculate_frequency(lotto_df):
    numbers = lotto_df.values.flatten().tolist()
    freq = {i: numbers.count(i) for i in range(1, 46)}
    return freq

# 🎯 추천 번호 (비례 or 역비례)
def recommend_numbers(lotto_df, proportional=True):
    freq = calculate_frequency(lotto_df)
    max_freq = max(freq.values())
    weighted = [
        num for num, count in freq.items()
        for _ in range(count if proportional else max_freq - count + 1)
    ]
    weighted = list(set(weighted))
    if len(weighted) < 6:
        return []
    return sorted(random.sample(weighted, 6))

# 🧠 AI 추천 기능
def train_rf_model(df):
    if len(df) < 2:
        return None
    X = df.iloc[:-1].values
    y = df.iloc[1:].values
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def ai_recommend(sets=1):
    df = load_data()
    model = train_rf_model(df)
    if model is None:
        return []
    return [model.predict(df.sample(n=1).values)[0].tolist() for _ in range(sets)]
