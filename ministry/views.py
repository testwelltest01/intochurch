import os
import json
import urllib.request
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from .models import WeeklyReport, FinancialTransaction, ChurchReview, NotionNotice # NotionNotice 추가 확인

def home(request):
    today = timezone.now().date()

    # --- [IP 주소 가져오기] ---
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # 오늘 리뷰 작성 여부 확인
    has_reviewed_today = ChurchReview.objects.filter(ip_address=client_ip, created_at__date=today).exists()

    # --- [0. 리뷰 작성 처리] ---
    if request.method == 'POST':
        author_name = request.POST.get('author_name')
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        
        if author_name and content and not has_reviewed_today:
            ChurchReview.objects.create(
                author_name=author_name,
                rating=rating,
                content=content,
                ip_address=client_ip
            )
        return redirect('home')

    # --- [1. 통계 및 차트 데이터] ---
    last_report = WeeklyReport.objects.filter(date__lte=today).order_by('-date').first()
    recent_reports = WeeklyReport.objects.filter(date__lte=today).order_by('-date')[:4]
    recent_reports_reversed = reversed(list(recent_reports))
    
    chart_labels = [r.date.strftime('%m/%d') for r in recent_reports_reversed]
    chart_data = [r.worship_attendance for r in reversed(list(recent_reports))]

    stat = None
    if last_report:
        stat = {
            'worship_attendance': last_report.worship_attendance,
            'new_comers': last_report.new_comers,
            'offering_total': last_report.offering_total,
            'date': last_report.date
        }

    # --- [2. 메인 슬라이드] ---
    slides = []
    slides_dir = os.path.join(settings.BASE_DIR, 'static', 'slides')
    if os.path.exists(slides_dir):
        file_list = sorted([f for f in os.listdir(slides_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])
        title_list = [
            "영원한 것을 위해 영원하지 않은 것을 희생하려고 합니다.",
            "모든 사람이 죄를 범하였으매 하나님의 영광에 이르지 못하더니",
            "우리가 아직 죄인되었을 때에 그리스도께서 우리를 위하여 죽으심으로\n하나님께서 우리에 대한 자기의 사랑을 확증하셨느니라",
            "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니\n이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라",
            "새 계명을 너희에게 주노니 서로 사랑하라\n내가 너희를 사랑한 것 같이 너희도 서로 사랑하라"
        ]
        for idx, filename in enumerate(file_list):
            current_title = title_list[idx] if idx < len(title_list) else ""
            slides.append({
                'id': idx, 
                'title': current_title, 
                'image': {'url': f"/static/slides/{filename}"}
            })

    # --- [3. 재정 내역 페이지네이션] ---
    all_transactions = FinancialTransaction.objects.order_by('-transaction_date')
    tx_paginator = Paginator(all_transactions, 10)
    recent_transactions = tx_paginator.get_page(request.GET.get('tx_page', 1))

    if request.headers.get('HX-Request') and 'tx_page' in request.GET:
        return render(request, 'ministry/partials/transaction_list.html', {'transactions': recent_transactions})

    # --- [4. 리뷰 페이지네이션] ---
    all_reviews = ChurchReview.objects.order_by('-created_at')
    review_paginator = Paginator(all_reviews, 6)
    recent_reviews = review_paginator.get_page(request.GET.get('review_page', 1))

    if request.headers.get('HX-Request') and 'review_page' in request.GET:
        return render(request, 'ministry/partials/review_list.html', {'reviews': recent_reviews})

    # --- [5. 노션 데이터 동기화 및 서버 DB 로드] ---
    # 1. 우리 DB에서 먼저 가져옵니다 (매우 빠름)
    notion_notices_qs = NotionNotice.objects.all().order_by('-date')
    if not notion_notices_qs.exists():
        try:
            # ... (API 호출 및 json_data 로드 로직 동일) ...
            for page in json_data['results']:
                props = page['properties']
                title = props['이름']['title'][0]['plain_text'] if props['이름']['title'] else "제목 없음"
                date_val = props['날짜']['date']['start'] if props['날짜']['date'] else str(timezone.now().date())
                
                # 본문 텍스트 합치기
                text_val = "".join([t['plain_text'] for t in props['텍스트']['rich_text']]) if props['텍스트']['rich_text'] else ""
                
                # 파일 정보 추출 및 JSON 변환
                files = []
                if '파일과 미디어' in props and props['파일과 미디어']['files']:
                    for f in props['파일과 미디어']['files']:
                        url = f['file']['url'] if 'file' in f else f['external']['url']
                        files.append({'name': f.get('name', '첨부파일'), 'url': url})
                
                # DB에 저장 (files_json 필드에 리스트를 문자열로 저장)
                NotionNotice.objects.get_or_create(
                    title=title, 
                    date=date_val, 
                    defaults={
                        'content': text_val,
                        'files_json': json.dumps(files)
                    }
                )
            # --- [5. 노션 데이터 동기화 및 서버 DB 로드] ---
    notion_notices_qs = NotionNotice.objects.all().order_by('-date')

    # 데이터가 없으면 즉시 동기화 시도
    if not notion_notices_qs.exists():
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
                # 날짜 기준 내림차순 정렬 요청
                payload = json.dumps({"sorts": [{"property": "날짜", "direction": "descending"}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                
                with urllib.request.urlopen(req) as response:
                    json_data = json.loads(response.read().decode("utf-8"))
                    
                    for page in json_data.get('results', []):
                        props = page.get('properties', {})
                        
                        # 1. 제목 추출
                        title_list = props.get('이름', {}).get('title', [])
                        title = title_list[0]['plain_text'] if title_list else "제목 없음"
                        
                        # 2. 날짜 추출
                        date_info = props.get('날짜', {}).get('date')
                        date_val = date_info['start'] if date_info else str(timezone.now().date())
                        
                        # 3. 본문 텍스트 추출
                        rich_text = props.get('텍스트', {}).get('rich_text', [])
                        text_val = "".join([t['plain_text'] for t in rich_text])
                        
                        # 4. 파일 및 미디어 추출
                        files_data = props.get('파일과 미디어', {}).get('files', [])
                        file_list = []
                        for f in files_data:
                            f_url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                            if f_url:
                                file_list.append({'name': f.get('name', '첨부파일'), 'url': f_url})
                        
                        # DB 저장 (이미 있으면 건너뜀)
                        NotionNotice.objects.get_or_create(
                            title=title,
                            date=date_val,
                            defaults={
                                'content': text_val,
                                'files_json': json.dumps(file_list) # 리스트를 글자 형태로 저장
                            }
                        )
                # 저장 후 다시 불러오기
                notion_notices_qs = NotionNotice.objects.all().order_by('-date')
        except Exception as e:
            print(f"❌ 동기화 실패: {e}")
        except Exception as e:
            print(f"❌ 동기화 실패: {e}")

    # 3. 페이지네이션 처리
    notion_paginator = Paginator(notion_notices_qs, 6)
    recent_notices = notion_paginator.get_page(request.GET.get('notion_page', 1))

    if request.headers.get('HX-Request') and 'notion_page' in request.GET:
        return render(request, 'ministry/partials/notion_list.html', {'notion_notices': recent_notices})

    # --- [최종 렌더링] ---
    return render(request, 'ministry/dashboard.html', {
        'stat': stat,
        'slides': slides,
        'transactions': recent_transactions,
        'reviews': recent_reviews,
        'notion_notices': recent_notices,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'has_reviewed_today': has_reviewed_today,
    })