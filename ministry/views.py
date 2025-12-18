import os
import json # 👈 이 줄이 반드시 있어야 합니다!
import urllib.request
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from .models import WeeklyReport, FinancialTransaction, ChurchReview, NotionNotice

def home(request):
    today = timezone.now().date()
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')).split(',')[0]
    has_reviewed_today = ChurchReview.objects.filter(ip_address=client_ip, created_at__date=today).exists()

    # --- [0. 리뷰 처리] ---
    if request.method == 'POST':
        author_name = request.POST.get('author_name')
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        if author_name and content and not has_reviewed_today:
            ChurchReview.objects.create(author_name=author_name, rating=rating, content=content, ip_address=client_ip)
        return redirect('home')

    # --- [1. 통계/차트/슬라이드] (기존 로직 동일하게 유지) ---
    last_report = WeeklyReport.objects.filter(date__lte=today).order_by('-date').first()
    recent_reports = WeeklyReport.objects.filter(date__lte=today).order_by('-date')[:4]
    chart_labels = [r.date.strftime('%m/%d') for r in reversed(list(recent_reports))]
    chart_data = [r.worship_attendance for r in reversed(list(recent_reports))]
    stat = {'worship_attendance': last_report.worship_attendance, 'new_comers': last_report.new_comers, 'offering_total': last_report.offering_total, 'date': last_report.date} if last_report else None

    slides = []
    slides_dir = os.path.join(settings.BASE_DIR, 'static', 'slides')
    if os.path.exists(slides_dir):
        file_list = sorted([f for f in os.listdir(slides_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        title_list = ["영원한 것을 위해 영원하지 않은 것을 희생하려고 합니다.", "모든 사람이 죄를 범하였으매 하나님의 영광에 이르지 못하더니", "우리가 아직 죄인되었을 때에 그리스도께서 우리를 위하여 죽으심으로\n하나님께서 우리에 대한 자기의 사랑을 확증하셨느니라", "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니\n이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라", "새 계명을 너희에게 주노니 서로 사랑하라\n내가 너희를 사랑한 것 같이 너희도 서로 사랑하라"]
        for idx, filename in enumerate(file_list):
            slides.append({'id': idx, 'title': title_list[idx] if idx < len(title_list) else "", 'image': {'url': f"/static/slides/{filename}"}})

    # --- [2. 페이지네이션 (재정/리뷰)] ---
    recent_transactions = Paginator(FinancialTransaction.objects.order_by('-transaction_date'), 10).get_page(request.GET.get('tx_page', 1))
    if request.headers.get('HX-Request') and 'tx_page' in request.GET:
        return render(request, 'ministry/partials/transaction_list.html', {'transactions': recent_transactions})

    recent_reviews = Paginator(ChurchReview.objects.order_by('-created_at'), 6).get_page(request.GET.get('review_page', 1))
    if request.headers.get('HX-Request') and 'review_page' in request.GET:
        return render(request, 'ministry/partials/review_list.html', {'reviews': recent_reviews})

    # --- [3. 노션 동기화 (초고속 DB 방식)] ---
    # 먼저 DB를 확인합니다.
    notion_notices_qs = NotionNotice.objects.all().order_by('-date')

    # 만약 데이터가 없으면 '딱 한 번만' 노션에서 긁어와 저장합니다.
    if not notion_notices_qs.exists():
        try:
            api_key = os.environ.get("NOTION_API_KEY")
            db_id = os.environ.get("NOTION_DATABASE_ID")
            if api_key and db_id:
                url = f"https://api.notion.com/v1/databases/{db_id}/query"
                headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
                payload = json.dumps({"sorts": [{"property": "날짜", "direction": "descending"}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req) as response:
                    results = json.loads(response.read().decode("utf-8")).get('results', [])
                    for page in results:
                        p = page.get('properties', {})
                        title = p['이름']['title'][0]['plain_text'] if p.get('이름') and p['이름']['title'] else "제목 없음"
                        date_v = p['날짜']['date']['start'] if p.get('날짜') and p['날짜']['date'] else str(today)
                        text_v = "".join([t['plain_text'] for t in p['텍스트']['rich_text']]) if p.get('텍스트') and p['텍스트']['rich_text'] else ""
                        
                        # 파일 정보 추출
                        files = []
                        for f in p.get('파일과 미디어', {}).get('files', []):
                            f_url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                            if f_url: files.append({'name': f.get('name', '첨부파일'), 'url': f_url})
                        
                        NotionNotice.objects.get_or_create(title=title, date=date_v, defaults={'content': text_v, 'files_json': json.dumps(files)})
                notion_notices_qs = NotionNotice.objects.all().order_by('-date')
        except Exception as e:
            print(f"Notion Sync Error: {e}")

    # DB에 저장된 JSON 문자열을 템플릿에서 쓸 수 있게 리스트로 미리 변환
    for notice in notion_notices_qs:
        try:
            notice.files = json.loads(notice.files_json)
        except:
            notice.files = []

    recent_notices = Paginator(notion_notices_qs, 6).get_page(request.GET.get('notion_page', 1))
    if request.headers.get('HX-Request') and 'notion_page' in request.GET:
        return render(request, 'ministry/partials/notion_list.html', {'notion_notices': recent_notices})

    return render(request, 'ministry/dashboard.html', {
        'stat': stat, 'slides': slides, 'transactions': recent_transactions, 
        'reviews': recent_reviews, 'notion_notices': recent_notices,
        'chart_labels': chart_labels, 'chart_data': chart_data, 'has_reviewed_today': has_reviewed_today,
    })