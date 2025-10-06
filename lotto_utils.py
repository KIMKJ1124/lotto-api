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
    """9999 회차 요청을 통해 최신 회차 번호를 빠르게 확인"""
    try:
        url = f"{BASE_URL}&drwNo=9999"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                return data.get("drwNo")
        return None
    except Exception as e:
        print(f"❌ 최신 회차 조회 실패: {e}")
        return None


# ----------------------------------
# 🔹 특정 회차 데이터 가져오기
# ----------------------------------
def get_round(round_no):
    """지정된 회차의 로또 당첨 데이터를 반환"""
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
    """
    Render 환경에서는 전체 회차를 불러오면 메모리 초과 발생하므로
    최신 회차부터 최근 limit_rounds 개만 수집
    """
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
        time.sleep(0.1)  # 과도한 요청 방지 (100ms 대기)

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
    """이미 저장된 CSV 파일을 로드"""
    if not os.path.exists(DATA_FILE):
        print("⚠️ CSV 파일이 존재하지 않습니다.")
        return None
    try:
        df = pd.read_csv(DATA_FILE)
        return df
    except Exception as e:
        print(f"❌ CSV 파일 로드 실패: {e}")
        return None


# ----------------------------------
# 🔹 추천번호 생성 로직
# ----------------------------------
def get_recommendations(mode="proportional", sets=5):
    """
    mode:
      - proportional : 빈도 기반 가중치 추천
      - random : 단순 랜덤
    """
    df = load_existing_data()
    if df is None or df.empty:
        raise ValueError("데이터가 로드되지 않았습니다.")

    # 숫자별 등장 빈도 계산
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
            # 빈도 기반 가중 랜덤 추출
            picks = random.choices(all_numbers, weights=weights, k=6)
            picks = sorted(list(set(picks)))  # 중복 제거
            while len(picks) < 6:
                picks.append(random.choice(all_numbers))
                picks = sorted(list(set(picks)))
        else:
            # 완전 랜덤
            picks = sorted(random.sample(all_numbers, 6))
        results.append(picks)

    return results
