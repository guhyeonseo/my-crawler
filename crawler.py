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

collection.create_index("link", unique=True)

def fetch_headlines(page):
    url = f"https://news.naver.com/section/105?page={page}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

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


def run_crawler():
    print("\n===== 크롤링 시작 =====")
    for p in range(1, 6):
        print(f"크롤링 {p} 페이지")
        headlines = fetch_headlines(p)

        for item in headlines:
            try:
                collection.insert_one(item)
                print("저장됨:", item["title"])
            except errors.DuplicateKeyError:
                print("중복 스킵:", item["title"])
    print("===== 크롤링 종료 =====\n")


def start_crawler_background():
    def job():
        run_crawler()
        schedule.every(60).seconds.do(run_crawler)

        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=job)
    thread.daemon = True
    thread.start()
