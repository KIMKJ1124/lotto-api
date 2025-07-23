import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import os

XLSX_FILE = "lotto_data.xlsx"

def fetch_lotto_data(start=1, end=1181):
    url = "https://www.dhlottery.co.kr/gameResult.do?method=byWin"
    all_rounds = []

    for round_no in range(start, end + 1):
        print(f"{round_no}회차 수집 중...")  # 진행 메시지
        params = {"drwNo": round_no}
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        numbers = soup.select(".ball_645")
        if len(numbers) >= 6:
            all_rounds.append([int(n.text) for n in numbers[:6]])

    print("✅ 모든 회차 수집 완료")
    return all_rounds

def save_lotto_data(data):
    df = pd.DataFrame(data)
    df.to_excel(XLSX_FILE, index=False, engine="openpyxl")

def load_data():
    if not os.path.exists(XLSX_FILE):
        print("데이터 파일이 없어 웹에서 수집합니다...")
        data = fetch_lotto_data()
        save_lotto_data(data)

    df = pd.read_excel(XLSX_FILE, engine="openpyxl")
    return df

def calculate_frequency(lotto_df):
    numbers = lotto_df.values.flatten().tolist()
    freq = {i: numbers.count(i) for i in range(1, 46)}
    return freq

def recommend_numbers(lotto_df, proportional=True):
    freq = calculate_frequency(lotto_df)
    max_freq = max(freq.values())

    weighted = [
        num for num, count in freq.items()
        for _ in range(count if proportional else max_freq - count + 1)
    ]
    weighted = list(set(weighted))  # 중복 제거

    if len(weighted) < 6:
        return []

    return sorted(random.sample(weighted, 6))