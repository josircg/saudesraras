from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Section, Page, Article

class SectionForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='admin'), required=False)
    header = forms.CharField(widget=CKEditorWidget(config_name='admin'), required=False)

    class Meta:
        model = Section
        fields = ['title', 'order', 'header', 'content', 'visible']


class PageForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='admin'), required=False)

    class Meta:
        model = Page
        fields = ['title', 'content', 'image']


class ArticleForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='admin'), required=False)
    header = forms.CharField(widget=CKEditorWidget(config_name='admin'), required=False)

    class Meta:
        model = Article
        fields = ['title', 'order', 'header', 'content']