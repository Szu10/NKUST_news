import feedparser
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# Securely load credentials from GitHub Secrets
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')

KEYWORDS = '"國立高雄科技大學" OR "高科大" OR "NKUST" OR "高雄科技大學" OR "高雄科大"'

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
        link = entry.link
        pub_date = entry.published
        
        news_items.append({'title': title, 'agency': source, 'link': link, 'date': pub_date})
        
    return news_items

def send_email(news_items):
    if not news_items:
        print("今天沒有找到相關的新聞。")
        return

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"NKUST新聞日報 - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    html_content = "<h2>NKUST每日新聞彙整</h2><hr>"
    for item in news_items:
        html_content += f"""
        <div style='margin-bottom: 20px;'>
            <h3 style='margin: 0;'><a href='{item['link']}'>{item['title']}</a></h3>
            <p style='margin: 5px 0; color: #555;'>
                <strong>來源:</strong> {item['agency']} <br>
                <strong>日期:</strong> {item['date']}
            </p>
        </div>
        """
        
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    news_data = fetch_nkust_news()
    send_email(news_data)
