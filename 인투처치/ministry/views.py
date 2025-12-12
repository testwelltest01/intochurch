import os
import json
import urllib.request
from django.shortcuts import render
from django.utils import timezone
from .models import WeeklyReport, FinancialTransaction, SlideImage, ChurchReview

def home(request):
    # --- 1. 기존 통계 데이터 처리 ---
    today = timezone.now().date()
    last_report = WeeklyReport.objects.filter(date__lte=today).order_by('-date').first()
    
    
    # --- 1-1. 차트용 최근 4주 데이터 ---
    recent_reports = WeeklyReport.objects.filter(date__lte=today).order_by('-date')[:4]
    # 차트는 왼쪽(과거) -> 오른쪽(최신)으로 그려져야 하므로 뒤집습니다.
    recent_reports_reversed = reversed(list(recent_reports))
    
    chart_labels = []
    chart_data = []
    
    for r in recent_reports_reversed:
        chart_labels.append(r.date.strftime('%m/%d')) # 예: 12/07
        chart_data.append(r.worship_attendance)

    stat = None
    if last_report:
        stat = {
            'worship_attendance': last_report.worship_attendance,
            'new_comers': last_report.new_comers,
            'offering_total': last_report.offering_total,
            'date': last_report.date
        }

    # --- 2. 메인 슬라이드 사진 ---
    slides = SlideImage.objects.filter(is_active=True).order_by('order')

    # --- 3. 최근 재정 내역 (5개) ---
    recent_transactions = FinancialTransaction.objects.order_by('-transaction_date')[:5]

    # --- 4. 최근 리뷰 (3개) ---
    recent_reviews = ChurchReview.objects.order_by('-created_at')[:3]

    # --- 5. [업그레이드] 노션 모든 데이터 가져오기 ---
    notion_notices = []
    try:
        api_key = os.environ.get("NOTION_API_KEY")
        db_id = os.environ.get("NOTION_DATABASE_ID")

        if api_key and db_id:
            url = f"https://api.notion.com/v1/databases/{db_id}/query"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28", 
                "Content-Type": "application/json"
            }
            # 날짜 최신순 정렬
            payload = {
                "page_size": 5,
                "sorts": [{"property": "날짜", "direction": "descending"}]
            }
            data = json.dumps(payload).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode("utf-8")
                json_data = json.loads(response_body)
                
                for page in json_data['results']:
                    props = page['properties']
                    
                    # 1. 이름 (제목)
                    title = "제목 없음"
                    if '이름' in props and props['이름']['title']:
                        title = props['이름']['title'][0]['plain_text']
                    
                    # 2. 날짜
                    date_str = ""
                    if '날짜' in props and props['날짜']['date']:
                        date_str = props['날짜']['date']['start']

                    # 3. 텍스트 (본문 내용)
                    text_content = ""
                    if '텍스트' in props and props['텍스트']['rich_text']:
                        # 여러 줄일 경우를 대비해 합칩니다
                        text_content = "".join([t['plain_text'] for t in props['텍스트']['rich_text']])

                    # 4. 파일과 미디어 (다운로드 링크)
                    file_url = ""
                    file_name = ""
                    if '파일과 미디어' in props and props['파일과 미디어']['files']:
                        file_info = props['파일과 미디어']['files'][0]
                        file_name = file_info.get('name', '첨부파일')
                        # 노션에 직접 올린 파일 vs 외부 링크 구분
                        if 'file' in file_info:
                            file_url = file_info['file']['url']
                        elif 'external' in file_info:
                            file_url = file_info['external']['url']

                    notion_notices.append({
                        'title': title,
                        'date': date_str,
                        'text': text_content, # 추가됨
                        'file_url': file_url, # 추가됨
                        'file_name': file_name, # 추가됨
                        'url': page['url']
                    })
                    
            print(f"✅ 노션 데이터 {len(notion_notices)}개 로드 완료!")
            
    except Exception as e:
        print(f"❌ 노션 연동 오류: {e}")

    return render(request, 'ministry/dashboard.html', {
        'stat': stat,
        'slides': slides,
        'transactions': recent_transactions,
        'reviews': recent_reviews,
        'notion_notices': notion_notices,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })