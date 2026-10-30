import os
import json # 👈 이 줄이 반드시 있어야 합니다!
import urllib.request
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.vary import vary_on_headers
from .models import WeeklyReport, FinancialTransaction, ChurchReview, NotionNotice

SLIDE_TITLES = ["영원한 것을 위해 영원하지 않은 것을 희생하려고 합니다.", "모든 사람이 죄를 범하였으매 하나님의 영광에 이르지 못하더니", "우리가 아직 죄인되었을 때에 그리스도께서 우리를 위하여 죽으심으로\n하나님께서 우리에 대한 자기의 사랑을 확증하셨느니라", "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니\n이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라", "새 계명을 너희에게 주노니 서로 사랑하라\n내가 너희를 사랑한 것 같이 너희도 서로 사랑하라"]


# ==========================================
# 공통 헬퍼 (여러 화면에서 같이 씁니다)
# ==========================================

def _client_ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')).split(',')[0]


def _latest_stat(today):
    last_report = WeeklyReport.objects.filter(date__lte=today).order_by('-date').first()
    if not last_report:
        return None
    return {'worship_attendance': last_report.worship_attendance, 'new_comers': last_report.new_comers, 'offering_total': last_report.offering_total, 'date': last_report.date}


def _attendance_chart(today):
    recent_reports = list(reversed(list(WeeklyReport.objects.filter(date__lte=today).order_by('-date')[:4])))
    return [r.date.strftime('%m/%d') for r in recent_reports], [r.worship_attendance for r in recent_reports]


def _slides():
    slides = []
    slides_dir = os.path.join(settings.BASE_DIR, 'static', 'slides')
    if os.path.exists(slides_dir):
        file_list = sorted([f for f in os.listdir(slides_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        for idx, filename in enumerate(file_list):
            slides.append({'id': idx, 'title': SLIDE_TITLES[idx] if idx < len(SLIDE_TITLES) else "", 'image': {'url': f"/static/slides/{filename}"}})
    return slides


def _sync_notion_if_empty(today):
    # 노션 동기화 (초고속 DB 방식)
    # DB에 데이터가 없으면 '딱 한 번만' 노션에서 긁어와 저장합니다.
    if NotionNotice.objects.exists():
        return
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
    except Exception as e:
        print(f"Notion Sync Error: {e}")


def _notices(today):
    _sync_notion_if_empty(today)
    return NotionNotice.objects.all().order_by('-date')


def _attach_files(page):
    # DB에 저장된 JSON 문자열을 템플릿에서 쓸 수 있게 리스트로 미리 변환
    page.object_list = list(page.object_list)
    for notice in page.object_list:
        try:
            notice.files = json.loads(notice.files_json)
        except:
            notice.files = []


# ==========================================
# 하단 탭 화면들
# ==========================================

def home(request):
    today = timezone.now().date()
    chart_labels, chart_data = _attendance_chart(today)
    return render(request, 'ministry/home.html', {
        'slides': _slides(), 'stat': _latest_stat(today),
        'chart_labels': chart_labels, 'chart_data': chart_data,
        'latest_notices': _notices(today)[:3],
    })


@vary_on_headers('HX-Request')
def news(request):
    notices = Paginator(_notices(timezone.now().date()), 6).get_page(request.GET.get('page', 1))
    _attach_files(notices)
    if request.headers.get('HX-Request'):
        return render(request, 'ministry/partials/notion_list.html', {'notion_notices': notices})
    return render(request, 'ministry/news.html', {'notion_notices': notices})


@vary_on_headers('HX-Request')
def finance(request):
    transactions = Paginator(FinancialTransaction.objects.order_by('-transaction_date'), 10).get_page(request.GET.get('page', 1))
    if request.headers.get('HX-Request'):
        return render(request, 'ministry/partials/transaction_list.html', {'transactions': transactions})
    return render(request, 'ministry/finance.html', {'transactions': transactions, 'stat': _latest_stat(timezone.now().date())})


@vary_on_headers('HX-Request')
def reviews(request):
    today = timezone.now().date()
    client_ip = _client_ip(request)
    has_reviewed_today = ChurchReview.objects.filter(ip_address=client_ip, created_at__date=today).exists()

    if request.method == 'POST':
        author_name = request.POST.get('author_name')
        content = request.POST.get('content')
        try:
            rating = min(max(int(request.POST.get('rating', 5)), 1), 5)
        except (TypeError, ValueError):
            rating = 5
        if author_name and content and not has_reviewed_today:
            ChurchReview.objects.create(author_name=author_name, rating=rating, content=content, ip_address=client_ip)
        return redirect('reviews')

    review_page = Paginator(ChurchReview.objects.order_by('-created_at'), 6).get_page(request.GET.get('page', 1))
    if request.headers.get('HX-Request'):
        return render(request, 'ministry/partials/review_list.html', {'reviews': review_page})
    return render(request, 'ministry/reviews.html', {'reviews': review_page, 'has_reviewed_today': has_reviewed_today})


def location(request):
    return render(request, 'ministry/location.html')


def offline(request):
    return render(request, 'ministry/offline.html')


# ==========================================
# PWA (앱 설치 정보 + 서비스 워커)
# ==========================================

def manifest(request):
    return render(request, 'ministry/pwa/manifest.webmanifest', content_type='application/manifest+json')


def service_worker(request):
    # 서비스 워커는 사이트 전체를 관리해야 하므로 /static/ 이 아니라 /sw.js(루트)에서 내보냅니다.
    # 배포할 때마다 커밋 해시가 바뀌므로 캐시도 자동으로 새로 만들어집니다.
    cache_version = os.environ.get('VERCEL_GIT_COMMIT_SHA', 'dev')[:7]
    response = render(request, 'ministry/pwa/sw.js', {'cache_version': cache_version}, content_type='application/javascript')
    response['Cache-Control'] = 'no-cache'
    return response
