from django.db import models

# 1. 주간 사역 보고
class WeeklyReport(models.Model):
    date = models.DateField(verbose_name="기준 날짜(주일)")
    worship_attendance = models.IntegerField(verbose_name="예배 인원", default=0)
    new_comers = models.IntegerField(verbose_name="새가족 수", default=0)
    offering_total = models.BigIntegerField(verbose_name="주간 헌금 총액", default=0)

    def __str__(self):
        return f"{self.date} 사역 보고"
    
    class Meta:
        verbose_name = "주간 사역 보고서"
        verbose_name_plural = "주간 사역 보고서"

# 2. 재정 투명성 장부
class FinancialTransaction(models.Model):
    TYPE_CHOICES = (('IN', '수입'), ('OUT', '지출'))
    
    transaction_date = models.DateField(verbose_name="날짜") 
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name="구분")
    category = models.CharField(max_length=50, verbose_name="부서/항목")
    description = models.CharField(max_length=200, verbose_name="적요(내역)")
    amount = models.IntegerField(verbose_name="금액")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.transaction_date}] {self.description}"

    class Meta:
        verbose_name = "재정 입출금 내역"
        verbose_name_plural = "재정 입출금 내역"

# 3. 성도 리뷰
class ChurchReview(models.Model):
    author_name = models.CharField(max_length=20, default="익명", verbose_name="작성자")
    content = models.TextField(verbose_name="후기 내용")
    rating = models.IntegerField(default=5, verbose_name="별점(1-5)")
    
    # ▼▼▼ 이 줄을 추가하세요! (IP 주소 저장용) ▼▼▼
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="작성자 IP")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name} - {self.rating}점"

class Meta:
    verbose_name = "성도 리얼 리뷰"
    verbose_name_plural = "성도 리얼 리뷰"
    ordering = ['-created_at'] # 최신순 정렬 기본 적용

# 4. 메인 화면 슬라이드 이미지
class SlideImage(models.Model):
    title = models.CharField(max_length=50, verbose_name="사진 제목(설명)")
    image = models.ImageField(upload_to='slides/', verbose_name="슬라이드 사진")
    order = models.IntegerField(default=0, verbose_name="순서(낮은순)")
    is_active = models.BooleanField(default=True, verbose_name="노출 여부")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "메인 슬라이드 사진"
        verbose_name_plural = "메인 슬라이드 사진"