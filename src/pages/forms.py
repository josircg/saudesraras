from django import forms
from .models import Section, Page, Article

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = [ 'title', 'order', 'header', 'content', 'visible']

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title','content', 'image']

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'order', 'header', 'content']