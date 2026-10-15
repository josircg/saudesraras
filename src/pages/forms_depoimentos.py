from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Section

class DepoimentoForm(forms.ModelForm):
    profile_image = forms.ImageField(
        label='Foto de Perfil',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = Section
        fields = ['title', 'order', 'header', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 1}),
            'header': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': CKEditorWidget(config_name='default'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['header'].required = False
        self.fields['content'].required = False
        self.fields['order'].required = False