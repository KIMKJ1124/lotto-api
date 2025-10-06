import pandas as pd
import requests
import os
import random
from sklearn.ensemble import RandomForestClassifier

XLSX_FILE = "lotto_data.xlsx"

# 🔍 최신 회차 번호 가져오기
def get_latest_round():
    for round_no in range(2000, 0, -1):
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return round_no
    return None

# 📥 특정 범위 회차 수집
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

# 💾 데이터 저장
def save_lotto_data(data):
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["drwNo"]).sort_values("drwNo")
    df.to_excel(XLSX_FILE, index=False, engine="openpyxl")
    print(f"💾 {XLSX_FILE} 저장 완료 (총 {len(df)} 회차)")

# 📂 데이터 로딩
def load_data():
    if not os.path.exists(XLSX_FILE):
        print("📁 데이터 파일 없음 → 전체 회차 수집 시작")
        data = fetch_lotto_data()
        if data:
            save_lotto_data(data)
    else:
        df = pd.read_excel(XLSX_FILE, engine="openpyxl")
        if "drwNo" not in df.columns:
            print("❌ 'drwNo' 컬럼 없음 → 파일 재생성")
            data = fetch_lotto_data()
            if data:
                save_lotto_data(data)
        else:
            latest_local = int(df["drwNo"].max())
            latest_online = get_latest_round()
            if latest_online and latest_local < latest_online:
                print(f"📈 새로운 회차 발견: {latest_local+1} ~ {latest_online}")
                new_data = fetch_lotto_data(start=latest_local + 1, end=latest_online)
                if new_data:
                    all_data = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
                    save_lotto_data(all_data.to_dict(orient="records"))

    return pd.read_excel(XLSX_FILE, engine="openpyxl")

# 🎲 번호 빈도 계산
def calculate_frequency(df):
    numbers = df[["num1", "num2", "num3", "num4", "num5", "num6"]].values.flatten()
    freq = pd.Series(numbers).value_counts().to_dict()
    return freq

# 🎯 번호 추천 (비례/역비례)
def recommend_numbers(df, proportional=True):
    freq = calculate_frequency(df)
    weighted = []

    for num in range(1, 46):
        count = freq.get(num, 0)
        weight = count if proportional else (max(freq.values()) - count + 1)
        weighted.extend([num] * weight)

    if len(weighted) < 6:
        return []
    return sorted(random.sample(weighted, 6))

# 🤖 AI 추천 모델 학습
def train_rf_model(df):
    if len(df) < 2:
        raise ValueError("학습 데이터가 부족합니다. 최소 2개 이상의 회차가 필요합니다.")
    X = df[["num1", "num2", "num3", "num4", "num5", "num6"]].iloc[:-1]
    y = df[["num1", "num2", "num3", "num4", "num5", "num6"]].iloc[1:]
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)
    return model

# 🤖 AI 추천 실행
def ai_recommend(sets=1):
    df = load_data()
    if len(df) < 2:
        print("❌ AI 추천 불가: 데이터 부족")
        return []

    try:
        model = train_rf_model(df)
        last = df[["num1", "num2", "num3", "num4", "num5", "num6"]].iloc[-1].values.reshape(1, -1)
        predictions = model.predict(last)
        result = []
        for _ in range(sets):
            pred = predictions[0]
            if hasattr(pred, "tolist"):
                result.append(sorted(pred.tolist()))
            else:
                result.append(sorted(list(pred)))
        return result
    except Exception as e:
        print(f"❌ AI 추천 실패: {e}")
        return []
