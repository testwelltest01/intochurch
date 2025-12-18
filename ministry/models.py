from django.db import models

"""
models.py는 데이터의 '설계도(Schema)'를 만드는 곳입니다.
여기서 클래스(Class)를 하나 만들면, 데이터베이스에 엑셀 시트(Table)가 하나 생긴다고 생각하면 쉽습니다.
각 변수들은 엑셀의 '열(Column)' 제목이 됩니다.
"""

# ----------------------------------------------------------------------------------------
# 1. 주간 사역 보고 (모델 = 데이터베이스 테이블)
# ----------------------------------------------------------------------------------------
class WeeklyReport(models.Model): # 모든 모델은 models.Model을 상속받아야 합니다.
    
    # models.DateField: 날짜를 저장하는 칸입니다. (년-월-일)
    # verbose_name: 관리자 화면에서 사람에게 보여질 친절한 이름입니다.
    date = models.DateField(verbose_name="기준 날짜(주일)")
    
    # models.IntegerField: 숫자를 저장하는 칸입니다.
    # default=0: 입력하지 않으면 자동으로 0이 들어갑니다.
    worship_attendance = models.IntegerField(verbose_name="예배 인원", default=0)
    new_comers = models.IntegerField(verbose_name="새가족 수", default=0)
    
    # models.BigIntegerField: 아주 큰 숫자를 저장할 때 씁니다. (헌금 액수는 클 수 있으니까요!)
    offering_total = models.BigIntegerField(verbose_name="주간 헌금 총액", default=0)

    # __str__ 함수 (매직 메서드)
    # 이 데이터의 '이름표'를 달아주는 역할입니다.
    # 관리자 목록이나 터미널에서 데이터를 조회할 때 "WeeklyReport object (1)" 대신 "2024-12-11 사역 보고"라고 예쁘게 나옵니다.
    def __str__(self):
        return f"{self.date} 사역 보고"
    
    # Meta 클래스: 모델 자체에 대한 설정을 담습니다.
    class Meta:
        verbose_name = "주간 사역 보고서"       # 단수형 이름
        verbose_name_plural = "주간 사역 보고서" # 복수형 이름 (Django는 자동으로 s를 붙이는데, 한글은 똑같이 해주는 게 좋습니다)


# ----------------------------------------------------------------------------------------
# 2. 재정 투명성 장부
# ----------------------------------------------------------------------------------------
class FinancialTransaction(models.Model):
    # 선택지(Choices) 정의: 드롭다운 메뉴처럼 고를 수 있게 만듭니다.
    # 왼쪽: 실제 DB에 저장될 값 ('IN', 'OUT') / 오른쪽: 화면에 보일 값 ('수입', '지출')
    TYPE_CHOICES = (('IN', '수입'), ('OUT', '지출'))
    
    transaction_date = models.DateField(verbose_name="날짜") 
    
    # models.CharField: 짧은 글자(문자열)를 저장합니다.
    # max_length: 최대 글자 수를 제한합니다 (필수!). DB 용량을 아끼기 위함입니다.
    # choices: 미리 정해둔 선택지 중에서만 고를 수 있게 제한합니다.
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name="구분")
    
    category = models.CharField(max_length=50, verbose_name="부서/항목")
    description = models.CharField(max_length=200, verbose_name="적요(내역)")
    amount = models.IntegerField(verbose_name="금액")
    
    # auto_now_add=True: 데이터가 처음 생성될 때의 시간을 자동으로 찍습니다.
    # 우리가 직접 입력하는 게 아니라, 시스템이 알아서 기록하는 '생성일자'입니다.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.transaction_date}] {self.description}"

    class Meta:
        verbose_name = "재정 입출금 내역"
        verbose_name_plural = "재정 입출금 내역"


# ----------------------------------------------------------------------------------------
# 3. 성도 리뷰
# ----------------------------------------------------------------------------------------
class ChurchReview(models.Model):
    author_name = models.CharField(max_length=20, default="익명", verbose_name="작성자")
    
    # models.TextField: 아주 긴 글을 저장할 때 씁니다. (길이 제한이 거의 없습니다)
    content = models.TextField(verbose_name="후기 내용")
    
    rating = models.IntegerField(default=5, verbose_name="별점(1-5)")
    
    # models.GenericIPAddressField: IP 주소(예: 192.168.0.1)를 저장하는 전용 필드입니다.
    # null=True, blank=True: 값이 비어있어도 괜찮다는 뜻입니다. (선택사항)
    # 중복 투표 방지 등을 위해 IP를 기록할 때 씁니다.
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="작성자 IP")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name} - {self.rating}점"

    class Meta:
        verbose_name = "성도 리얼 리뷰"
        verbose_name_plural = "성도 리얼 리뷰"
        # ordering: 데이터를 불러올 때 기본 정렬 순서를 정합니다.
        # '-created_at': created_at 앞에 '-'가 붙으면 역순(내림차순)입니다. 즉, 최신 글이 먼저 보입니다.
        ordering = ['-created_at'] 


# ----------------------------------------------------------------------------------------
# 4. 메인 화면 슬라이드 이미지
# ----------------------------------------------------------------------------------------
class SlideImage(models.Model):
    title = models.CharField(max_length=50, verbose_name="사진 제목(설명)")
    
    # models.ImageField: 이미지 파일을 업로드하고 관리하는 필드입니다.
    # upload_to='slides/': 이미지가 저장될 'media/slides/' 폴더를 지정합니다.
    image = models.ImageField(upload_to='slides/', verbose_name="슬라이드 사진")
    
    order = models.IntegerField(default=0, verbose_name="순서(낮은순)")
    
    # models.BooleanField: 참(True) 또는 거짓(False)만 저장하는 필드입니다. (체크박스)
    # 이미지를 삭제하지 않고 잠시 숨기고 싶을 때 유용합니다.
    is_active = models.BooleanField(default=True, verbose_name="노출 여부")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "메인 슬라이드 사진"
        verbose_name_plural = "메인 슬라이드 사진"

class NotionNotice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    # 파일 정보를 저장할 필드
    files_json = models.TextField(blank=True, default="[]") 
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']