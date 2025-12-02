from flask import Flask, jsonify
from pymongo import MongoClient
from crawler import start_crawler_background
import os

app = Flask(__name__)

# 🔥 MongoDB Atlas 연결
MONGO_URI = "mongodb+srv://myuser:mypassword123!@cluster0.sqzxe33.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["newsdb"]
collection = db["news"]

# 🔥 Render 웹 서버가 켜질 때 백그라운드 크롤러 자동 실행
start_crawler_background()


@app.route("/")
def home():
    return {"message": "API 서버 + 크롤러 정상 작동 중"}


@app.route("/news")
def get_news():
    data = list(collection.find({}, {"_id": 0}).sort("created_at", -1))
    return jsonify(data)


if __name__ == "__main__":
    # Render에서 PORT 환경변수 사용 필수
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
