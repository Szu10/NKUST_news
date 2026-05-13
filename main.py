import feedparser
import urllib.parse
import smtplib
import requests
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import os

# ── 環境變數 ──────────────────────────────────────────────────────────────────
SENDER_EMAIL   = os.environ.get('SENDER_EMAIL')
APP_PASSWORD   = os.environ.get('APP_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')

# ── 啟動前確認環境變數都存在，缺少任何一個就直接報錯，方便 debug ────────────
if not all([SENDER_EMAIL, APP_PASSWORD, RECEIVER_EMAIL]):
    raise ValueError(
        "缺少必要的環境變數，請確認 GitHub Secrets 中已設定: "
        "SENDER_EMAIL, APP_PASSWORD, RECEIVER_EMAIL"
    )

KEYWORDS = '"國立高雄科技大學" OR "高科大" OR "NKUST" OR "高雄科大" OR "高雄科技大學"'


def get_original_url(google_url):
    """模擬瀏覽器點擊，獲取跳轉後的真實新聞網址。
    若 Google 未成功跳轉（仍停在 news.google.com），則回傳原始網址。"""
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        response = requests.get(
            google_url, headers=headers, allow_redirects=True, timeout=10
        )
        # 若仍在 Google News 頁面，代表跳轉失敗，回傳原始網址
        if 'news.google.com' in response.url:
            return google_url
        return response.url
    except Exception as e:
        print(f"解析網址失敗，使用原網址: {e}")
        return google_url


def fetch_nkust_news():
    """從 Google News RSS 抓取昨天到今天的 NKUST 相關新聞。"""
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz)

    # FIX: 原本 before 用 today，導致只抓到昨天且容易漏掉當天新聞。
    #      改為 before = tomorrow，確保整個昨天與今天都涵蓋在內。
    yesterday_str = (now_tw - timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow_str  = (now_tw + timedelta(days=1)).strftime('%Y-%m-%d')

    search_query  = f'{KEYWORDS} after:{yesterday_str} before:{tomorrow_str}'
    encoded_query = urllib.parse.quote(search_query)
    rss_url = (
        f"https://news.google.com/rss/search?q={encoded_query}"
        f"&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    )

    print(f"抓取 RSS: {rss_url}")
    feed = feedparser.parse(rss_url)
    news_items = []

    for entry in feed.entries:
        full_title   = entry.title
        title_parts  = full_title.rsplit(' - ', 1)
        title        = title_parts[0] if len(title_parts) > 0 else full_title
        source       = title_parts[1] if len(title_parts) > 1 else "來源不明"
        google_link  = entry.link

        print(f"正在處理: {title[:30]}...")
        real_link = get_original_url(google_link)

        raw_date   = entry.published
        clean_date = " ".join(raw_date.split()[:4])

        news_items.append({
            'title'  : title,
            'agency' : source,
            'link'   : real_link,
            'date'   : clean_date,
        })

        time.sleep(0.5)   # 縮短等待時間，節省 Actions 執行分鐘數

    return news_items


def send_email(news_items):
    """將新聞清單組成 HTML 信件並寄出；無新聞時也寄出通知信。"""
    tw_tz      = timezone(timedelta(hours=8))
    today_date = datetime.now(tw_tz).strftime('%Y-%m-%d')

    receiver_list = [email.strip() for email in RECEIVER_EMAIL.split(',')]

    msg             = MIMEMultipart("alternative")
    msg['From']     = SENDER_EMAIL
    msg['To']       = ", ".join(receiver_list)

    # ── 無新聞時仍寄一封通知，避免靜默失敗 ─────────────────────────────────
    if not news_items:
        print("今天沒有找到相關新聞，寄出通知信。")
        msg['Subject'] = f"NKUST新聞日報 - {today_date}（今日無新聞）"
        html_content   = (
            "<h2>高科大每日新聞彙整</h2><hr>"
            "<p>今日未找到符合條件的相關新聞。</p>"
        )
        msg.attach(MIMEText(html_content, "html"))
    else:
        msg['Subject'] = f"NKUST新聞日報 - {today_date}"
        html_content   = "<h2>高科大每日新聞彙整</h2><hr>"
        for item in news_items:
            html_content += f"""
        <div style='margin-bottom: 25px;'>
            <h3 style='margin: 0;'>
                <a href='{item['link']}'>{item['title']}</a>
            </h3>
            <p style='margin: 5px 0; color: #555; line-height: 1.5;'>
                <strong>來源：</strong> {item['agency']} <br>
                <strong>時間：</strong> {item['date']}
            </p>
        </div>
            """
        msg.attach(MIMEText(html_content, "html"))

    # ── 寄信 ─────────────────────────────────────────────────────────────────
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_list, msg.as_string())
        server.quit()
        print(f"信件已發送至: {', '.join(receiver_list)}")
    except Exception as e:
        print(f"發送失敗: {e}")
        raise   # 重新拋出例外，讓 GitHub Actions 標記為失敗，方便排查


if __name__ == "__main__":
    news_data = fetch_nkust_news()
    send_email(news_data)
