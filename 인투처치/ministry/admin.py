import pandas as pd
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse # <--- 파일 다운로드를 위해 필요!
from .models import WeeklyReport, FinancialTransaction, ChurchReview, SlideImage
from .forms import ExcelUploadForm

@admin.register(FinancialTransaction)
class FinancialAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'type', 'category', 'description', 'amount')
    list_filter = ('transaction_date', 'type', 'category')
    search_fields = ('description', 'category')
    change_list_template = "ministry/admin_changelist.html"

    # ▼▼▼ 1. 관리자 목록에서 선택할 수 있는 '액션'에 함수 등록 ▼▼▼
    actions = ['export_to_excel']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('upload-excel/', self.upload_excel),]
        return my_urls + urls

    def upload_excel(self, request):
        # ... (기존 업로드 로직 그대로 유지) ...
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES["excel_file"]
                try:
                    df = pd.read_excel(excel_file)
                    count = 0
                    for index, row in df.iterrows():
                        type_code = 'IN' if row['구분'] == '수입' else 'OUT'
                        FinancialTransaction.objects.create(
                            transaction_date=row['날짜'],
                            type=type_code,
                            category=row['부서'],
                            description=row['내역'],
                            amount=row['금액']
                        )
                        count += 1
                    self.message_user(request, f"{count}건 등록 완료")
                    return redirect("..")
                except Exception as e:
                    self.message_user(request, f"에러: {e}", level=messages.ERROR)
        form = ExcelUploadForm()
        payload = {"form": form}
        return render(request, "ministry/admin_excel_upload.html", payload)

    # ▼▼▼ 2. 엑셀 다운로드 기능 구현 (핵심 로직) ▼▼▼
    @admin.action(description='📊 선택한 내역을 엑셀로 내보내기')
    def export_to_excel(self, request, queryset):
        # (1) 선택된 데이터(queryset)를 리스트로 변환
        data = []
        for tx in queryset:
            data.append({
                '날짜': tx.transaction_date,
                '구분': tx.get_type_display(), # 'IN' 대신 '수입'으로 저장
                '부서': tx.category,
                '내역': tx.description,
                '금액': tx.amount
            })

        # (2) 판다스 데이터프레임 만들기
        df = pd.DataFrame(data)

        # (3) 엑셀 파일로 변환하여 브라우저에게 응답(Response)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=financial_report.xlsx'
        
        # 판다스의 to_excel 기능을 이용해 response 객체에 바로 씀
        df.to_excel(response, index=False)
        
        return response

# 나머지 모델 등록
admin.site.register(WeeklyReport)
admin.site.register(ChurchReview)
admin.site.register(SlideImage)