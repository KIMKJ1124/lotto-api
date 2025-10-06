import pandas as pd
import requests
import os
import random
from sklearn.ensemble import RandomForestClassifier  # AI 추천용

XLSX_FILE = "lotto_data.xlsx"



# 🔍 최신 회차 번호 가져오기
def get_latest_round():
    # 대략 1100회 이상 진행되었으므로, 1200부터 역순으로 확인
    for round_no in range(2000, 0, -1):
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return round_no
    return None

def fetch_lotto_data(start=1, end=None):
    if end is None:
        end = get_latest_round()
    if not end:
        print("❌ 최신 회차 조회 실패")
        return []

    url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber"
    all_rounds = []

    for round_no in range(start, end + 1):
        response = requests.get(url, params={"drwNo": round_no})
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                all_rounds.append({
                    "drwNo": data["drwNo"],
                    "num1": data["drwtNo1"],
                    "num2": data["drwtNo2"],
                    "num3": data["drwtNo3"],
                    "num4": data["drwtNo4"],
                    "num5": data["drwtNo5"],
                    "num6": data["drwtNo6"],
                    "bonus": data["bnusNo"]
                })
                print(f"✅ {round_no}회차 저장 완료")
            else:
                print(f"⚠️ {round_no}회차 데이터 없음")

    return all_rounds

# 💾 안전한 저장
def save_lotto_data(data):
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["drwNo"]).sort_values("drwNo")
    df.to_excel(XLSX_FILE, index=False, engine="openpyxl")
    print(f"💾 {XLSX_FILE} 저장 완료 (총 {len(df)} 회차)")

# 📥 데이터 로딩 (없으면 자동 수집 + 최신 회차 갱신)
def load_data():
    if not os.path.exists(XLSX_FILE):
        print("데이터 파일이 없어 전체 회차 수집합니다...")
        data = fetch_lotto_data()
        if data:
            save_lotto_data(data)
    else:
        df = pd.read_excel(XLSX_FILE, engine="openpyxl")
        latest_local = int(df["drwNo"].max())  # 마지막 저장된 회차
        latest_online = get_latest_round()

        if latest_online and latest_local < latest_online:
            print(f"📈 새로운 회차 발견! {latest_local+1} ~ {latest_online}회차 수집 중...")
            new_data = fetch_lotto_data(start=latest_local + 1, end=latest_online)
            if new_data:
                all_data = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
                save_lotto_data(all_data.to_dict(orient="records"))

    return pd.read_excel(XLSX_FILE, engine="openpyxl")

# 🎲 번호 빈도 계산
def calculate_frequency(df):
    numbers = df[["num1","num2","num3","num4","num5","num6"]].values.flatten()
    freq = pd.Series(numbers).value_counts().to_dict()
    return freq

# 🎯 번호 추천 (비례/역비례)
def recommend_numbers(df, mode="proportional"):
    freq = calculate_frequency(df)

    weighted = []
    for num in range(1, 46):
        count = freq.get(num, 0)
        weight = count if mode == "proportional" else (max(freq.values()) - count + 1)
        weighted.extend([num] * weight)

    if len(weighted) < 6:
        return []
    return sorted(random.sample(weighted, 6))

# 🤖 AI 추천 (랜덤포레스트 분류기)
def train_rf_model(df):
    X = df[["num1","num2","num3","num4","num5","num6"]].iloc[:-1]
    y = df[["num1","num2","num3","num4","num5","num6"]].iloc[1:]
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)
    return model

def ai_recommend(df):
    model = train_rf_model(df)
    last = df[["num1","num2","num3","num4","num5","num6"]].iloc[-1].values.reshape(1, -1)
    pred = model.predict(last)[0]
    return sorted(pred.tolist())
