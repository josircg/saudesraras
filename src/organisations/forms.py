from django import forms
from django_select2.forms import Select2MultipleWidget
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from .models import Organisation, OrganisationType
from projects.forms import getCountryCode
from ckeditor.widgets import CKEditorWidget


class OrganisationForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        label=_('Organisation name'),
        help_text=_('Please write the name of the organisation or network.'),
        widget=forms.TextInput())
    url = forms.URLField(
        max_length=200,
        label=_('URL'),
        help_text=_('Please provide the URL to the website of the organisation.'),
        widget=forms.TextInput())
    description = forms.CharField(
        help_text=_('Please briefly describe the organisation (max 500 words).'),
        widget=CKEditorWidget(config_name='frontpage'),
        label=_('Description'),
        max_length=3000)
    orgType = forms.ModelChoiceField(
        queryset=OrganisationType.objects.none(),
        label=_("Type"),
        help_text=_('Please select one.'),
        widget=forms.Select(attrs={'class': 'js-example-basic-single'}))
    logo = forms.ImageField(
        required=False,
        help_text=_("The image (.jpg or .png) will be resized to 600 x 400 pixels."
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"),
        widget=forms.FileInput(attrs={'data-image-suffix': '', 'data-image-width-option': 0}))
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)
    contact_point = forms.CharField(
        max_length=100,
        help_text=_('Please name the contact person or contact point for the organisation.'),
        label=_('Organisation contact point'),
        widget=forms.TextInput())
    contact_point_email = forms.EmailField(
        max_length=100,
        label=_('Contact point email'),
        help_text=_('Please provide the email address of the contact person or contact point.'),
        widget=forms.TextInput())

    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.HiddenInput(),
        required=True)

    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.HiddenInput(),
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orgType'].queryset = OrganisationType.objects.translated_sorted_by_text()

    def clean_latitude(self):
        if not self.cleaned_data['latitude']:
            raise ValidationError("A marcação da localização no mapa é obrigatória")

    def save(self, args, logo_path):
        pk = self.data.get('organisationID', '')
        orgType = get_object_or_404(OrganisationType, id=self.data['orgType'])
        if pk:
            organisation = get_object_or_404(Organisation, id=pk)
            organisation.name = self.data['name']
            organisation.url = self.cleaned_data['url']
            organisation.description = self.data['description']
            organisation.orgType = orgType
            organisation.contactPoint = self.data['contact_point']
            organisation.contactPointEmail = self.data['contact_point_email']
            organisation.latitude = self.data['latitude']
            organisation.longitude = self.data['longitude']
            organisation.approved = self.data.get('approved', organisation.approved)
        else:
            organisation = Organisation(
                name=self.data['name'],
                url=self.cleaned_data['url'],
                creator=args.user,
                latitude=self.data['latitude'],
                longitude=self.data['longitude'],
                description=self.data['description'],
                orgType=orgType,
                contactPoint=self.data['contact_point'],
                contactPointEmail=self.data['contact_point_email'])

        if logo_path:
            organisation.logo = logo_path
        country = getCountryCode(organisation.latitude, organisation.longitude)
        organisation.country = country
        organisation.save()
        return organisation


class OrganisationPermissionForm(forms.Form):
    selectedUsers = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersCollection = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersAllowed = forms.MultipleChoiceField(
        choices=(),
        widget=Select2MultipleWidget,
        required=False,
        label=_("Give additional users permission to edit"))
