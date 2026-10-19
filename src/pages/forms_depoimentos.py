
from django import forms
import re
from ckeditor.widgets import CKEditorWidget
from .models import Section, img_finder, iframe_finder


class DepoimentoForm(forms.ModelForm):
    profile_image = forms.ImageField(
        label='Foto de Perfil (Avatar)',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    image_1 = forms.ImageField(
        label='Imagem Extra 1',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    image_2 = forms.ImageField(
        label='Imagem Extra 2',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    image_3 = forms.ImageField(
        label='Imagem Extra 3',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    image_4 = forms.ImageField(
        label='Imagem Extra 4',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    image_5 = forms.ImageField(
        label='Imagem Extra 5',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    remove_profile_image = forms.BooleanField(
        required=False,
        label='Excluir foto de perfil'
    )
    remove_image_1 = forms.BooleanField(
        required=False,
        label='Excluir foto extra 1'
    )
    remove_image_2 = forms.BooleanField(
        required=False,
        label='Excluir foto extra 2'
    )
    remove_image_3 = forms.BooleanField(
        required=False,
        label='Excluir foto extra 3'
    )
    remove_image_4 = forms.BooleanField(
        required=False,
        label='Excluir foto extra 4'
    )
    remove_image_5 = forms.BooleanField(
        required=False,
        label='Excluir foto extra 5'
    )

    video_url = forms.URLField(
        label='Link do Vídeo do Google Drive',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://drive.google.com/file/d/.../view?usp=sharing'
        })
    )

    class Meta:
        model = Section
        fields = ['title', 'order', 'header', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu Nome / Título'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Ordem de exibição (ex: 1)'
            }),
            'header': CKEditorWidget(config_name='default'),
            'content': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['header'].required = False
        self.fields['content'].required = False
        self.fields['order'].required = False

        self.existing_avatar = None
        self.existing_gallery = []
        self.existing_video = None

        if self.instance and self.instance.pk:
            self.initial['header'] = self.instance.clean_text_content()

            raw_video_url = self.instance.get_video_url()
            self.existing_video = raw_video_url

            if raw_video_url:
                drive_match = re.search(
                    r'/d/([a-zA-Z0-9_-]+)',
                    raw_video_url
                )

                if drive_match:
                    file_id = drive_match.group(1)
                    self.initial['video_url'] = (
                        f'https://drive.google.com/file/d/{file_id}/view'
                    )
                else:
                    self.initial['video_url'] = raw_video_url

            images = img_finder.findall(
                self.instance.header or ''
            )

            if images:
                self.existing_avatar = images[0]
                self.existing_gallery = images[1:]
