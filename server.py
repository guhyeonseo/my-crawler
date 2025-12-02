from flask import Flask, jsonify
from pymongo import MongoClient
from crawler import start_crawler_background

app = Flask(__name__)

MONGO_URI = "mongodb+srv://myuser:mypassword123!@cluster0.sqzxe33.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["newsdb"]
collection = db["news"]

# 백그라운드로 크롤러 시작
start_crawler_background()

@app.route("/")
def home():
    return {"message": "Crawler + API 서버 정상 작동 중"}

@app.route("/news")
def get_news():
    data = list(collection.find({}, {"_id": 0}).sort("created_at", -1))
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
