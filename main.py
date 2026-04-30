import feedparser
import urllib.parse
import smtplib
import requests  # 新增的套件，用來解析真實網址
import time      # 新增的套件，用來稍微暫停避免被 Google 封鎖
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')

KEYWORDS = '"國立高雄科技大學" OR "高科大" OR "NKUST" OR "高雄科大" OR "高雄科技大學"'

def get_original_url(google_url):
    """模擬瀏覽器點擊，獲取跳轉後的真實新聞網址"""
    try:
        # 偽裝成一般 Chrome 瀏覽器，避免被 Google 擋下
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # 發送請求，allow_redirects=True 會自動跟著 Google 跳轉到最終的新聞網頁
        response = requests.get(google_url, headers=headers, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"解析網址失敗，使用原網址: {e}")
        return google_url # 如果解析失敗，至少保留原本的 Google 連結當作備用

def fetch_nkust_news():
    encoded_query = urllib.parse.quote(KEYWORDS)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}%20when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries:
        full_title = entry.title
        title_parts = full_title.rsplit(' - ', 1)
        
        title = title_parts[0] if len(title_parts) > 0 else full_title
        source = title_parts[1] if len(title_parts) > 1 else "Unknown Agency"
        
        # 取得原本的 Google 網址
        google_link = entry.link
        
        # 呼叫我們寫好的函數，把 Google 網址轉換成真實網址
        print(f"正在解析真實網址: {title[:15]}...")
        real_link = get_original_url(google_link)
        
        pub_date = entry.published
        
        news_items.append({'title': title, 'agency': source, 'link': real_link, 'date': pub_date})
        
        # 每次解析完暫停 1 秒，不要頻繁連線以免被 Google 當成惡意攻擊阻擋
        time.sleep(1)
        
    return news_items

def send_email(news_items):
    if not news_items:
        print("今天沒有找到相關的新聞。")
        return

    receiver_list = [email.strip() for email in RECEIVER_EMAIL.split(',')]

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"NKUST新聞日報 - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(receiver_list)

    html_content = "<h2>高科大每日新聞彙整</h2><hr>"
    for item in news_items:
        html_content += f"""
        <div style='margin-bottom: 25px; line-height: 1.6; font-size: 15px;'>
            <strong style='font-size: 18px;'>{item['title']}</strong><br>
            <a href='{item['link']}' style='word-break: break-all;'>{item['link']}</a><br>
            <strong>來源：</strong> {item['agency']}<br>
            <strong>時間：</strong> {item['date']}
        </div>
        """
        
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_list, msg.as_string())
        server.quit()
        print(f"信件已成功發送至: {', '.join(receiver_list)}!")
    except Exception as e:
        print(f"發送失敗: {e}")

if __name__ == "__main__":
    news_data = fetch_nkust_news()
    send_email(news_data)
