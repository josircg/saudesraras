from __future__ import unicode_literals

from ckeditor.widgets import CKEditorWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django_select2 import forms as s2forms

from . import models

User = get_user_model()


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(Field("name"))
        self.helper.layout = Layout(Field("email"))
        self.fields['name'].label = _('First Name and Surname')

    class Meta:
        model = User
        fields = ["name", "email"]


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("title"),
            Field("country"),
            Field("picture"),
            Field("bio"),
            Field("orcid"),
            Field("interestAreas"),
            Field("latitude"),
            Field("longitude"),
            Submit("update", "Update", css_class="btn-green"),
        )

    bio = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        max_length=2000,
        required=False)
    interestAreas = forms.ModelMultipleChoiceField(
        queryset=models.InterestArea.objects.all(),
        widget=s2forms.ModelSelect2TagWidget(
            search_fields=['interestArea__icontains'],
            blank_label=_('None'),
            attrs={
                'data-token-separators': '[","]'}),
        required=False,
        label=_('Interest Areas'),
        help_text=_("Please write or select 2 to 3 interest areas, separated by commas or by "
                    "pressing enter"))
    country = CountryField(blank=True).formfield()
    country.label = _('Country')

    class Meta:
        model = models.Profile
        fields = ["picture", "title", "bio", "orcid", "interestAreas"]

    def save(self, args):
        pForm = super(ProfileForm, self).save(commit=False)
        pForm.user = args.user
        pForm.interestAreas.set(self.data.getlist('interestAreas'))
        pForm.country = self.data['country']
        pForm.save()
        return 'success'
