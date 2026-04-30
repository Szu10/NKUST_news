import feedparser
import urllib.parse
import smtplib
import requests  
import time      
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone  # 新增 timedelta 與 timezone 處理時區
import os

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')

KEYWORDS = '"國立高雄科技大學" OR "高科大" OR "NKUST" OR "高雄科大" OR "高雄科技大學"'

def get_original_url(google_url):
    """模擬瀏覽器點擊，獲取跳轉後的真實新聞網址"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(google_url, headers=headers, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"解析網址失敗，使用原網址: {e}")
        return google_url

def fetch_nkust_news():
    # --- 新增：設定台灣時區 (UTC+8)，並自動計算昨天與今天 ---
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz)
    yesterday_str = (now_tw - timedelta(days=1)).strftime('%Y-%m-%d')
    today_str = now_tw.strftime('%Y-%m-%d')
    
    # 把原本的 KEYWORDS 加上精確的日期範圍
    # 組合出來會像是: "..." after:2026-04-29 before:2026-04-30 (這樣會剛好抓滿 4/29 整天)
    search_query = f'{KEYWORDS} after:{yesterday_str} before:{today_str}'
    encoded_query = urllib.parse.quote(search_query)
    
    # 網址拿掉 when:1d，改用上面組合好的精確條件
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    # --------------------------------------------------------
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries:
        full_title = entry.title
        title_parts = full_title.rsplit(' - ', 1)
        
        title = title_parts[0] if len(title_parts) > 0 else full_title
        source = title_parts[1] if len(title_parts) > 1 else "來源不明"
        
        google_link = entry.link
        print(f"正在處理: {title[:15]}...")
        
        real_link = get_original_url(google_link)
        
        raw_date = entry.published  
        clean_date = " ".join(raw_date.split()[:4])
        
        news_items.append({
            'title': title, 
            'agency': source, 
            'link': real_link, 
            'date': clean_date
        })
        
        time.sleep(1)
        
    return news_items

def send_email(news_items):
    if not news_items:
        print("今天沒有找到相關新聞。")
        return

    receiver_list = [email.strip() for email in RECEIVER_EMAIL.split(',')]
    
    # 寄信時的標題也改用台灣時區，確保顯示的日期不會因為伺服器時差出錯
    tw_tz = timezone(timedelta(hours=8))
    today_date = datetime.now(tw_tz).strftime('%Y-%m-%d')

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"NKUST新聞日報 - {today_date}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(receiver_list)

    html_content = "<h2>高科大每日新聞彙整</h2><hr>"
    for item in news_items:
        html_content += f"""
        <div style='margin-bottom: 25px;'>
            <h3 style='margin: 0;'><a href='{item['link']}'>{item['title']}</a></h3>
            <p style='margin: 5px 0; color: #555; line-height: 1.5;'>
                <strong>來源：</strong> {item['agency']} <br>
                <strong>時間：</strong> {item['date']}
            </p>
        </div>
        """
        
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_list, msg.as_string())
        server.quit()
        print(f"信件已發送至: {', '.join(receiver_list)}")
    except Exception as e:
        print(f"發送失敗: {e}")

if __name__ == "__main__":
    news_data = fetch_nkust_news()
    send_email(news_data)
