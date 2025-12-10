from django import forms
from .models import ChurchReview

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="엑셀 파일 선택")

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ChurchReview
        fields = ['author_name', 'content', 'rating']