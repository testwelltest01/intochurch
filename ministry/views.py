import os
import json
import urllib.request
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from .models import WeeklyReport, FinancialTransaction, SlideImage, ChurchReview

def home(request):
    today = timezone.now().date()

    # IP 주소 가져오기 (Helper)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0]
    else:
        client_ip = request.META.get('REMOTE_ADDR')

    # 오늘 리뷰 작성 여부 확인
    has_reviewed_today = ChurchReview.objects.filter(ip_address=client_ip, created_at__date=today).exists()

    # --- 0. 리뷰 작성 처리 (POST 요청) ---
    if request.method == 'POST':
        author_name = request.POST.get('author_name')
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        
        if author_name and content:
            # 1일 1회 작성 제한
            if not has_reviewed_today:
                ChurchReview.objects.create(
                    author_name=author_name,
                    rating=rating,
                    content=content,
                    ip_address=client_ip
                )
            return redirect('/#review-section')

    # --- 1. 기존 통계 데이터 처리 ---
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

# --- 2. 메인 슬라이드 사진 (GitHub 폴더 읽기 모드) ---
    from django.conf import settings
    import re
    
    slides = []
    # [핵심 변경] media 폴더가 아니라 static 폴더를 뒤집니다!
    # Vercel에 배포된 소스코드 내의 static 폴더 경로입니다.
    slides_dir = os.path.join(settings.BASE_DIR, 'static', 'slides')
    
    try:
        # 폴더가 있는지 확인
        if os.path.exists(slides_dir):
            file_list = sorted(os.listdir(slides_dir)) # 이름순 정렬
            
            for idx, filename in enumerate(file_list):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    
                    title = ['우리교회는', '이제 신설되었습니다.']
                    
                    slides.append({
                        'id': idx, 
                        'title': title, 
                        'image': {'url': f"/static/slides/{filename}"}
                    })
        else:
            print(f"⚠️ 경고: {slides_dir} 폴더를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 이미지 로드 실패: {e}")

    # --- 3. 최근 재정 내역 (페이지네이션: 10개씩) ---
    all_transactions = FinancialTransaction.objects.order_by('-transaction_date')
    tx_paginator = Paginator(all_transactions, 10)
    tx_page = request.GET.get('tx_page', 1)
    recent_transactions = tx_paginator.get_page(tx_page)

    # [HTMX] 재정 페이지네이션 요청인 경우 부분 템플릿만 렌더링
    if request.headers.get('HX-Request') and 'tx_page' in request.GET:
        return render(request, 'ministry/partials/transaction_list.html', {
            'transactions': recent_transactions
        })

    # --- 4. 최근 리뷰 (페이지네이션: 6개씩) ---
    all_reviews = ChurchReview.objects.order_by('-created_at')
    review_paginator = Paginator(all_reviews, 6)
    review_page = request.GET.get('review_page', 1)
    recent_reviews = review_paginator.get_page(review_page)

    # [HTMX] 리뷰 페이지네이션 요청인 경우 부분 템플릿만 렌더링
    if request.headers.get('HX-Request') and 'review_page' in request.GET:
        return render(request, 'ministry/partials/review_list.html', {
            'reviews': recent_reviews
        })

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
                    files = []
                    if '파일과 미디어' in props and props['파일과 미디어']['files']:
                        for f_info in props['파일과 미디어']['files']:
                            f_name = f_info.get('name', '첨부파일')
                            f_url = ""
                            if 'file' in f_info:
                                f_url = f_info['file']['url']
                            elif 'external' in f_info:
                                f_url = f_info['external']['url']
                            
                            if f_url:
                                files.append({
                                    'name': f_name,
                                    'url': f_url
                                })

                    notion_notices.append({
                        'title': title,
                        'date': date_str,
                        'text': text_content,
                        'files': files,
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
        'has_reviewed_today': has_reviewed_today,
    })