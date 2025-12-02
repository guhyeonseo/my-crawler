import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, errors
from datetime import datetime
import time

MONGO_URI = "mongodb+srv://myuser:mypassword123!@cluster0.sqzxe33.mongodb.net/?appName=Cluster0"

# -----------------------------
# 🚀 MongoDB 연결 (재시도 포함)
# -----------------------------
def connect_mongo():
    while True:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.server_info()  # 연결 테스트
            print("✅ MongoDB 연결 성공")
            return client
        except Exception as e:
            print("❌ MongoDB 연결 실패. 5초 후 재시도:", e)
            time.sleep(5)

client = connect_mongo()
db = client["newsdb"]
collection = db["news"]

collection.create_index("link", unique=True)


# -----------------------------
# 🚀 뉴스 크롤링 함수
# -----------------------------
def fetch_headlines(page):
    url = f"https://news.naver.com/section/105?page={page}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
        response.raise_for_status()
    except Exception as e:
        print(f"❌ 요청 실패 (page {page}):", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("li.sa_item")

    results = []

    for item in items:
        title_tag = item.select_one("a.sa_text_title")
        press_tag = item.select_one("div.sa_text_press")
        lede_tag = item.select_one("div.sa_text_lede")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = "https://news.naver.com" + title_tag.get("href")
        press = press_tag.get_text(strip=True) if press_tag else ""
        lede = lede_tag.get_text(strip=True) if lede_tag else ""

        results.append({
            "title": title,
            "link": link,
            "press": press,
            "lede": lede,
            "created_at": datetime.utcnow()
        })

    return results


# -----------------------------
# 🚀 전체 크롤링 실행
# -----------------------------
def run_crawler():
    print("\n===== 🔥 크롤링 시작 =====\n")

    for p in range(1, 11):
        print(f"➡ 페이지 {p} 수집 중...")
        headlines = fetch_headlines(p)

        for item in headlines:
            try:
                collection.insert_one(item)
                print("  ✔ 저장됨:", item["title"])
            except errors.DuplicateKeyError:
                print("  ↪ 중복 스킵:", item["title"])
            except Exception as e:
                print("  ❌ 저장 오류:", e)

    print("\n===== 🟢 크롤링 완료 =====\n")


# -----------------------------
# 🚀 Worker 메인 루프 (1분마다 실행)
# -----------------------------
if __name__ == "__main__":
    print("🚀 Render Worker: 자동 크롤러 실행 시작 (1분마다 반복)")

    while True:
        try:
            run_crawler()
        except Exception as e:
            print("❌ 실행 중 오류 발생:", e)

        print("⏳ 60초 대기...\n")
        time.sleep(60)
