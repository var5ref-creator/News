import feedparser
import requests
from googletrans import Translator
from bs4 import BeautifulSoup
import time
import re
import json
import os
from collections import deque

# -------- إعدادات البوت --------
BOT_TOKEN = "8732583795:AAGOcw2Yt7DxVnOtj42PFpPyfbfB0OARXOs"
CHAT_ID = -1003751243790

translator = Translator()

feeds = [
    ("🚨Bild", "https://rss.app/feeds/sHtp1E8HJ4etR8Sr.xml"),
    ("🚨Sky Sports", "https://rss.app/feeds/Qi5QR9xw2ULgMPIL.xml"),
    ("🚨BBC", "https://rss.app/feeds/wLHPubZUer1yvhGi.xml"),
    ("🚨TNT Sports", "https://rss.app/feeds/NOXGJ2t9hwRdWltn.xml"),
    ("🚨Kooora", "https://rss.app/feeds/ISHIbHWJLZzK8wTD.xml"),
    ("🚨The Guardian", "https://rss.app/feeds/DMZ7PzibgU91keBs.xml"),
    ("🚨The Sun", "https://rss.app/feeds/BCoxAgvFoKNZqO1z.xml"),
    ("🚨Fabrizio Romano", "https://rss.app/feeds/g998P6qr1gyZbrgk.xml"),
    ("🚨365Scores", "https://rss.app/feeds/D9X1vlOYx9K6gKJo.xml"),
    ("🚨Goal", "https://rss.app/feeds/52tPCTtjKrjyYTjO.xml"),

    ("🚨Kooora :", "https://rss.app/feeds/5oruNc27RMtV1oI2.xml"),
    ("🚨365Scores :", "https://rss.app/feeds/kGXAQMoxjrwBSlRd.xml"),
    ("🚨Transfermarkt", "https://rss.app/feeds/batQ4bGsVsGNzi4B.xml"),
    ("🚨AS", "https://rss.app/feeds/bjWiENpacnDs3dAA.xml"),
    ("🚨RMC Sport", "https://rss.app/feeds/BB7dLHET7viXXv5g.xml")
]

SENT_FILE = "sent_posts.json"

# -------- تحميل البيانات --------
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        sent_posts = {
            k: deque(v, maxlen=3) for k, v in data.items()
        }
else:
    sent_posts = {source[0]: deque(maxlen=3) for source in feeds}


# -------- دوال --------
def translate_ar(text):
    for _ in range(3):
        try:
            return translator.translate(text, dest="ar").text
        except:
            time.sleep(1)
    return text


def extract_image(post, desc_html):
    soup = BeautifulSoup(desc_html, "html.parser")

    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]

    if "media_content" in post:
        try:
            return post.media_content[0]["url"]
        except:
            pass

    if "links" in post:
        for link in post.links:
            if "image" in link.get("type", ""):
                return link.get("href")

    matches = re.findall(r'(https?://\S+\.(jpg|jpeg|png))', desc_html)
    if matches:
        return matches[0][0]

    return None


def send_to_telegram(text, image=None):
    try:
        if image:
            img_data = requests.get(image, timeout=10).content
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": text},
                files={"photo": img_data},
                timeout=15
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text},
                timeout=15
            )
    except Exception as e:
        print("خطأ إرسال:", e)


# -------- التشغيل --------
print("🚀 Bot Started...")

while True:
    try:
        for source_name, RSS_URL in feeds:
            print(f"🔎 Checking: {source_name}")

            feed = feedparser.parse(RSS_URL)

            if source_name not in sent_posts:
                sent_posts[source_name] = deque(maxlen=3)

            new_posts = []
            for post in feed.entries:
                post_id = post.get("id", post.get("link", post.get("title")))

                if post_id in sent_posts[source_name]:
                    break

                new_posts.append(post)

            new_posts = new_posts[:3]

            for post in reversed(new_posts):
                title = post.title
                desc_html = post.summary if "summary" in post else ""

                soup = BeautifulSoup(desc_html, "html.parser")
                desc = soup.get_text()
                desc = ' '.join(desc.split())

                image = extract_image(post, desc_html)

                title_ar = translate_ar(title)
                desc_ar = translate_ar(desc[:500])

                text = f"{source_name}\n\n{title_ar}\n\n{desc_ar}"

                send_to_telegram(text, image)

                sent_posts[source_name].appendleft(post.get("id", post.get("link", post.get("title"))))

        # حفظ
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            json.dump({k: list(v) for k, v in sent_posts.items()}, f, ensure_ascii=False)

        print("⏳ Waiting 60 sec...")
        time.sleep(60)  # مهم ل Render

    except Exception as e:
        print("🔥 Error in loop:", e)
        time.sleep(10)
