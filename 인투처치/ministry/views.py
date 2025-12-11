# ministry/views.py

from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator # 페이징 도구 (게시판 페이지 넘기는 기능)
from .models import WeeklyReport, FinancialTransaction, ChurchReview, SlideImage
from .forms import ReviewForm

"""
views.py는 '웹사이트의 로직(Logic)'을 담당하는 곳입니다.
사용자가 어떤 주소로 접속하면(Request), 그에 맞는 처리를 하고, 
결과 화면(Response)을 보여주는 함수(View Function)들이 모여 있습니다.
"""

def get_client_ip(request):
    """
    접속한 사용자의 IP 주소를 알아내는 도우미 함수입니다.
    리뷰 중복 작성을 방지하기 위해 사용합니다.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def dashboard(request):
    """
    메인 화면(대시보드)을 보여주는 메인 뷰 함수입니다.
    사용자가 홈페이지에 들어오면 이 함수가 실행됩니다.
    """
    
    # --- [1. 리뷰 작성 처리 (POST 요청)] ---
    # 사용자가 '작성 완료' 버튼을 눌러서 데이터를 보낼 때 (POST 방식)
    if request.method == 'POST':
        # 사용자가 입력한 데이터를 폼(Form)에 채워 넣습니다.
        form = ReviewForm(request.POST)
        
        # 입력한 내용에 문제가 없는지 검사합니다 (예: 내용이 비어있지 않은지).
        if form.is_valid():
            user_ip = get_client_ip(request) # IP 확인
            today = timezone.now().date()    # 오늘 날짜 확인
            
            # 오늘 이미 쓴 글이 있는지 DB에서 찾아봅니다. (같은 IP, 오늘 날짜)
            if ChurchReview.objects.filter(ip_address=user_ip, created_at__date=today).exists():
                # 이미 썼으면 에러 메시지를 띄웁니다.
                messages.error(request, "⚠️ 리뷰는 하루에 한 번만 등록할 수 있습니다.")
            else:
                # 문제 없으면 저장 준비!
                review = form.save(commit=False) # 바로 저장하지 않고 잠시 대기 (IP 주소 추가를 위해)
                review.ip_address = user_ip      # IP 주소를 채워 넣고
                review.save()                    # 진짜로 DB에 저장합니다.
                
                # 성공 메시지를 띄우고
                messages.success(request, "✅ 소중한 의견 감사합니다!")
                
                # 메인 화면('home')으로 새로고침(리다이렉트) 합니다.
                # 이걸 안 하면 '새로고침' 할 때마다 글이 또 써질 수 있습니다.
                return redirect('home')

    # --- [2. 데이터 조회 및 화면 보여주기 (GET 요청)] ---
    # 그냥 페이지에 접속했을 때 (GET 방식)
    
    # (1) 가장 최근 보고서와 슬라이드 사진 가져오기
    # WeeklyReport.objects.order_by('-date').first(): 날짜 내림차순(최신순)으로 정렬해서 첫 번째 것만 가져와라.
    latest_stat = WeeklyReport.objects.order_by('-date').first()
    # SlideImage.objects.filter(is_active=True): '사용 중(is_active=True)'인 사진들만 가져와라.
    slides = SlideImage.objects.filter(is_active=True).order_by('order')

    # (2) 재정 장부 페이지네이션 (1, 2, 3페이지...)
    all_transactions = FinancialTransaction.objects.order_by('-transaction_date')
    tx_paginator = Paginator(all_transactions, 10) # 한 페이지에 10개씩 자르기
    
    # 주소창의 ?tx_page=2 같은 파라미터를 읽습니다. 없으면 1페이지로 간주합니다.
    tx_page = request.GET.get('tx_page') 
    transactions = tx_paginator.get_page(tx_page) # 해당 페이지의 데이터만 가져옵니다.

    # (3) 리뷰 페이지네이션
    all_reviews = ChurchReview.objects.order_by('-created_at')
    review_paginator = Paginator(all_reviews, 10) # 10개씩 자르기
    
    # 리뷰는 ?review_page=2 처럼 다른 이름의 파라미터를 씁니다.
    # 그래야 재정 장부 페이지를 넘겼을 때 리뷰 페이지는 그대로 있을 수 있습니다.
    review_page = request.GET.get('review_page') 
    reviews = review_paginator.get_page(review_page)

    # context (꾸러미): HTML 파일로 보낼 데이터들을 딕셔너리에 담습니다.
    # HTML에서는 {{ stat }}, {{ reviews }} 처럼 여기서 정한 이름(Key)으로 꺼내 씁니다.
    context = {
        'stat': latest_stat,
        'transactions': transactions,
        'reviews': reviews,
        'slides': slides,
    }
    
    # render: 최종적으로 HTML 파일을 그려서 사용자에게 보내줍니다.
    # 'ministry/dashboard.html' 템플릿에 context 데이터를 섞어서 완성된 페이지를 만듭니다.
    return render(request, 'ministry/dashboard.html', context)