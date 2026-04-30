import os
import requests
import re
from datetime import datetime, timedelta

# 1. 설정 정보
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
SLACK_WEB_URL = os.environ.get('SLACK_WEB_URL')

def clean_html(text):
    if not text: return ""
    return re.sub('<.+?>', '', text).replace('&quot;', '"').replace('&amp;', '&')

def fetch_and_send_news():
    # 어제 날짜 계산 (예: 4월 30일 실행 시 4월 29일 기사만 찾음)
    yesterday = datetime.now() - timedelta(days=1)
    # 네이버 날짜 형식(Wed, 29 Apr 2026)과 비교하기 위한 필터
    date_filter = yesterday.strftime("%d %b %Y") 
    display_date = yesterday.strftime("%Y-%m-%d")

    query = "ROAI | 로아이"
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=50&sort=date"
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"네이버 API 에러: {response.status_code}")
        return

    items = response.json().get('items', [])
    
    # 🔍 어제 날짜 기사만 필터링
    yesterday_items = [item for item in items if date_filter in item['pubDate']]

    if not yesterday_items:
        # 🔔 뉴스가 없을 때 슬랙에 보낼 메시지 구성
        payload = {
            "text": f"📅 *{display_date}* 알림\n어제는 *'ROAI'* 관련 새로운 뉴스가 없습니다. ☕"
        }
        requests.post(SLACK_WEB_URL, json=payload)
        print(f"🔔 {display_date} 새로운 뉴스 없음 - 슬랙 알림 전송 완료")
        return

    attachments = []
    for item in yesterday_items:
        attachments.append({
            "title": clean_html(item['title']),
            "title_link": item['link'],
            "text": f"{clean_html(item['description'])}\n_{item['pubDate']}_",
            "color": "#36a64f"
        })

    payload = {
        "text": f"📅 *{display_date}* 전일 뉴스 요약 (총 {len(yesterday_items)}건)",
        "attachments": attachments
    }

    requests.post(SLACK_WEB_URL, json=payload)
    print(f"✅ {display_date} 뉴스 전송 완료!")

if __name__ == "__main__":
    fetch_and_send_news()
