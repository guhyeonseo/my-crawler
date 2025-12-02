import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, errors
from datetime import datetime
import schedule
import time
import threading

MONGO_URI = "mongodb+srv://myuser:mypassword123!@cluster0.sqzxe33.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["newsdb"]
collection = db["news"]

# link 중복 방지 인덱스 생성
collection.create_index("link", unique=True)


# 🔥 한 페이지 크롤링 함수
def fetch_headlines(page):
    url = f"https://news.naver.com/section/105?page={page}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        print("요청 오류:", e)
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


# 🔥 전체 페이지 크롤링
def run_crawler():
    print("\n===== 크롤링 시작 =====")
    try:
        for p in range(1, 6):
            print(f"크롤링 {p} 페이지")
            headlines = fetch_headlines(p)

            for item in headlines:
                try:
                    collection.insert_one(item)
                    print("저장됨:", item["title"])
                except errors.DuplicateKeyError:
                    print("중복 스킵:", item["title"])
    except Exception as e:
        print("크롤러 전체 오류:", e)

    print("===== 크롤링 종료 =====\n")


# 🔥 Render 무료 Sleep 방지용 ping
def keep_alive():
    try:
        requests.get("https://my-crawler-fv8n.onrender.com/", timeout=3)
        print("Keep-alive 요청 전송")
    except Exception as e:
        print("Keep-alive 실패:", e)


# 🔥 백그라운드 스레드 실행
def start_crawler_background():
    def job():
        print("백그라운드 스레드 시작됨")

        # 최초 1회 실행
        run_crawler()

        # 매 1분 크롤링
        schedule.every(60).seconds.do(run_crawler)

        # Render Sleep 방지
        schedule.every(10).minutes.do(keep_alive)

        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                print("스케줄 오류:", e)

            time.sleep(1)

    thread = threading.Thread(target=job)
    thread.daemon = True
    thread.start()
