from datetime import datetime

from authors.models import Author
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django_select2 import forms as s2forms
from django_select2.forms import Select2MultipleWidget
from organisations.models import Organisation
from projects.models import Project

from .models import Resource, Keyword, Category, Theme, ResourceGroup
from .models import ResourcesGrouped


class ResourceForm(forms.Form):
    # Main information
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(),
        label=_('Resource name'),
        help_text=_('Please write the title or name of the resource.'))

    url = forms.URLField(
        widget=forms.TextInput(),
        label=_('URL'),
        help_text=_(
            "Please provide the URL to where the material is available by the publisher, or "
            "in a permanent repository such as Zenodo, OSF, the RIO Journal, or similar."
        ))
    keywords = forms.ModelMultipleChoiceField(
        queryset=Keyword.objects.all(),
        widget=s2forms.ModelSelect2TagWidget(
            search_fields=['keyword__icontains'],
            attrs={
                'data-token-separators': '[","]'}),
        label=_('Keywords'),
        help_text=_("Please select or add 2 or 3 keywords <b>separated by commas or by "
                    "pressing enter</b>."),
        required=True)

    abstract = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_('Please briefly describe the resource (max 3000 characters).'),
        label=_('Brief description'),
        max_length=3000)

    description_citizen_science_aspects = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_(
            "Please describe the citizen science aspect(s) of the resource that "
            "warrant your registration in Civis. This information will not be "
            "visible on the platform, and serves simply as reference when undergoing "
            "moderation. You can see our explanation on what <a href=\"https://civis.ibict.br/"
            "about/\">citizen science</a> is (max 2000 characters)."),
        max_length=2000,
        label=_("Description of citizen science aspects"))

    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.all(),
        widget=s2forms.ModelSelect2TagWidget(
            search_fields=['author__icontains'],
            attrs={
                'data-token-separators': '[","]'}),
        help_text=_(
            "Please name the author(s) of the resource. Enter <i>First Initial Last Name</"
            "i> and close with a comma or press enter to add an author or multiple "
            "authors. If authorship is unknown, use the name of the project for which "
            "the resource was created."),
        required=False,
        label=_("Authors"))

    # To clasify
    # TODO: Improve category
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        label=_("Category"),
        help_text=_('Please select one of the proposed categories.'))
    choices = forms.CharField(widget=forms.HiddenInput(), required=False)
    categorySelected = forms.CharField(widget=forms.HiddenInput(), required=False)

    # audience = forms.ModelMultipleChoiceField(
    #         queryset=Audience.objects.all(),
    #         widget=Select2MultipleWidget(),
    #         label=_('Audience'),
    #         help_text=_(
    #             'Please select the audience(s) for which the resource is intended. '
    #             'Multiple options can be selected.'))

    theme = forms.ModelMultipleChoiceField(
        queryset=Theme.objects.none(),
        widget=Select2MultipleWidget(),
        label=_("Theme"),
        help_text=_('Please select the thematic content of the resource.'))

    resource_DOI = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(),
        help_text=_("Please provide the <b>Digital Object Identifier</b> that is unique to your "
                    "resource, created by publishers or repositories (Zenodo etc.)"),
        label=_('Resource DOI'))

    # TODO: Change this to be a year field
    year_of_publication = forms.IntegerField(
        required=False,
        widget=forms.TextInput(),
        label=_('Year of publication'),
        help_text=_('Please enter the year (YYYY) when this version of the resource was published.'))

    license = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'autocomplete': 'nope'}),
        help_text=_('Please indicate the resource license, such as Creative Commons CC-BY. '
                    'Enter a URL link to the license if available.'),
        label=_("License"),
        required=False)

    # Linking
    organisation = forms.ModelMultipleChoiceField(
        queryset=Organisation.objects.all(),
        widget=s2forms.ModelSelect2MultipleWidget(
            model=Organisation,
            search_fields=['name__icontains']),
        help_text=_(
            "Please select the organisation(s) contributing the resource, if any. If "
            "not listed, please add them <a href=\"/new_organisation\" target=\"_blank\">here</a > "
            "before submitting the resource."),
        required=False,
        label=_("Organisation(s)"))

    project = forms.ModelMultipleChoiceField(
        queryset=Project.objects.all(),
        widget=s2forms.ModelSelect2MultipleWidget(
            model=Project,
            search_fields=['name__icontains']),
        help_text=_(
            'Please select the project(s) where the resource was created. '
            'If not listed, please add them <a href="/newProject" '
            'target="_blank">here</a > before submitting.'),
        required=False,
        label=_("Project(s)"))

    publisher = forms.CharField(
        max_length=100,
        label=_("Publisher"),
        widget=forms.TextInput(),
        help_text=_('Please indicate the publisher of the resource'),
        required=False)

    # Images

    image1 = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'data-image-suffix': '1', 'data-image-width-option': 0}),
        label=_("Resource image for the thumbnail profile"),
        help_text=_("The image (.jpg or .png) will be resized to 600 x 400 pixels."
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"))
    image_credit1 = forms.CharField(max_length=300, required=False,
                                    label=_("Provide image credit, if applicable"))
    x1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    withImage1 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    image2 = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'data-image-suffix': '2', 'data-image-width-option': 1}),
        label=_("Image for the resource profile heading"),
        help_text=_("The image (.jpg or .png) will be resized to 1100x400 pixels. "
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"))
    image_credit2 = forms.CharField(max_length=300, required=False, label=_("Provide image credit, if applicable"))
    x2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    withImage2 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    # Curated list
    curatedList = forms.ModelMultipleChoiceField(
        queryset=ResourceGroup.objects.all(),
        widget=Select2MultipleWidget,
        required=False,
        label=_("Curated lists"))

    # Training resources fields

    time_required = forms.FloatField(required=False,
                                     help_text='Please write the approximate  hours required to finish the training.')
    conditions_of_access = forms.CharField(
        required=False,
        help_text='Please describe any conditions that affect the accessibility of the training material, '
                  'such as <i>requires registration</i>, <i>requires enrollment</i>, or <i>requires payment</i>.')

    isTrainingResource = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True).translated_sorted_by_text()
        self.fields['theme'].queryset = Theme.objects.translated_sorted_by_text()

    def save(self, args, images):
        """Save & update a Resource & Training Resource"""
        pk = self.data.get('resourceID', '')
        category = get_object_or_404(Category, id=self.data['category'])

        if pk:
            resource = get_object_or_404(Resource, id=pk)
            if resource.hidden:
                resource.hidden = False
            resource.name = self.data['name']
            resource.abstract = self.data['abstract']
            resource.description_citizen_science_aspects = self.data['description_citizen_science_aspects']
            resource.url = self.cleaned_data['url']
            resource.license = self.data['license']
            resource.publisher = self.data['publisher']
        else:
            resource = self.createResource(args)

        resource.inLanguage = self.data['language']
        resource.resourceDOI = self.data['resource_DOI']
        resource.save()
        if self.data['year_of_publication'] != '':
            resource.datePublished = self.data['year_of_publication']
        else:
            resource.datePublished = None
        resource.category = category

        # Saving images
        if (len(images[0]) > 6):
            resource.image1 = images[0]
        if (len(images[1]) > 6):
            resource.image2 = images[1]
        resource.imageCredit1 = self.data['image_credit1']
        resource.imageCredit2 = self.data['image_credit2']

        # Training resource fields

        # End training resource fields
        resource.save()

        # Set the fields that are lists
        resource.theme.set(self.data.getlist('theme'))
        resource.organisation.set(self.data.getlist('organisation'))
        resource.project.set(self.data.getlist('project'))
        resource.keywords.set(self.data.getlist('keywords'))
        curatedList = self.data.getlist('curatedList')

        if args.user.is_staff:
            objs = ResourcesGrouped.objects.filter(resource=resource)
            if objs:
                for obj in objs:
                    obj.delete()
            for clist in curatedList:
                resourceGroup = get_object_or_404(ResourceGroup, id=clist)
                ResourcesGrouped.objects.get_or_create(group=resourceGroup, resource=resource)

        return resource.id

    def createResource(self, args):
        return Resource(
            creator=args.user,
            name=self.data['name'],
            url=self.cleaned_data['url'],
            abstract=self.data['abstract'],
            description_citizen_science_aspects=self.data['description_citizen_science_aspects'],
            license=self.data['license'],
            publisher=self.data['publisher'],
            dateUploaded=datetime.now(),
            isTrainingResource=self.cleaned_data.get('isTrainingResource', False)
        )


class ResourcePermissionForm(forms.Form):
    selectedUsers = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersCollection = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersAllowed = forms.MultipleChoiceField(
        choices=(),
        widget=Select2MultipleWidget,
        required=False,
        label=_("Give additional users permission to edit"))
