# ministry/views.py

from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator # 페이징 도구
from .models import WeeklyReport, FinancialTransaction, ChurchReview, SlideImage
from .forms import ReviewForm

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def dashboard(request):
    # --- [1. 리뷰 작성 처리 (POST)] ---
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            user_ip = get_client_ip(request)
            today = timezone.now().date()
            if ChurchReview.objects.filter(ip_address=user_ip, created_at__date=today).exists():
                messages.error(request, "⚠️ 리뷰는 하루에 한 번만 등록할 수 있습니다.")
            else:
                review = form.save(commit=False)
                review.ip_address = user_ip
                review.save()
                messages.success(request, "✅ 소중한 의견 감사합니다!")
                return redirect('home')

    # --- [2. 데이터 조회 (GET)] ---
    
    # (1) 주간 보고 & 슬라이드
    latest_stat = WeeklyReport.objects.order_by('-date').first()
    slides = SlideImage.objects.filter(is_active=True).order_by('order')

    # (2) 재정 장부 페이지네이션 (변수명: tx_page)
    all_transactions = FinancialTransaction.objects.order_by('-transaction_date')
    tx_paginator = Paginator(all_transactions, 10) # 10개씩
    tx_page = request.GET.get('tx_page') # ★ 재정용 페이지 번호 받기
    transactions = tx_paginator.get_page(tx_page)

    # (3) 리뷰 페이지네이션 (변수명: review_page)
    all_reviews = ChurchReview.objects.order_by('-created_at')
    review_paginator = Paginator(all_reviews, 10) # 10개씩
    review_page = request.GET.get('review_page') # ★ 리뷰용 페이지 번호 받기 (이름 바꿈!)
    reviews = review_paginator.get_page(review_page)

    context = {
        'stat': latest_stat,
        'transactions': transactions,
        'reviews': reviews,
        'slides': slides,
    }
    return render(request, 'ministry/dashboard.html', context)