from accounts.models import ActivationTask
from ckeditor.widgets import CKEditorWidget
from django.conf import settings
from django.contrib.admin.models import ADDITION
from django.contrib.auth import get_user_model
from django.contrib.gis import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django_select2 import forms as s2forms
from django_select2.forms import Select2MultipleWidget
from django_summernote.widgets import SummernoteWidget
from eucs_platform.logger import log_message
from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim
from organisations.models import Organisation

from .models import ParticipationTask, TranslatedProject, ProjectPermission, Project, Topic, Status, Keyword, \
    FundingBody

geolocator = Nominatim(timeout=None, user_agent=settings.USER_AGENT)
USER = get_user_model()


def getCountryCode(latitude, longitude):
    try:
        if latitude and longitude:
            location = geolocator.reverse([latitude, longitude], exactly_one=True)
            if len(location.raw) > 1 and location.raw['address'].get('country_code'):
                return location.raw['address']['country_code'].upper()
        return ''
    except GeocoderServiceError:
        return ''


class ProjectGeographicLocationForm(forms.Form):
    projectGeographicLocation = forms.MultiPolygonField(
        required=False,
        widget=forms.OSMWidget(attrs={}),
        label=(' '))


class ProjectForm(forms.Form):
    # Main information
    project_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(),
        label=_("Project name"),
        help_text=_('Please write the name of the project.'))

    url = forms.URLField(
        max_length=200,
        widget=forms.TextInput(),
        label=_('URL'),
        help_text=_('Please provide the URL to the website of the project.'))

    description = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_("Please provide a description of your project here, featuring its "
                    "main goals and characteristics (max 3000 characters)."),
        label=_("Description"),
        max_length=3000)

    description_citizen_science_aspects = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_("Please describe the citizen science aspect(s) of the project that "
                    "warrant your registration in Civis. This information will not be "
                    "visible on the platform, and serves simply as reference when undergoing "
                    "moderation. You can see our explanation on what <a href=\"https://civis.ibict.br/"
                    "about/\">citizen science</a> is (max 2000 characters)."
                    ),
        max_length=2000,
        label=_('Description of citizen science aspects'))

    status = forms.ModelChoiceField(
        queryset=Status.objects.all(),
        label=_("Activity status"),
        widget=forms.Select(attrs={'class': 'js-example-basic-single'}),
        help_text=_('Please, select the status of your project.'))

    keywords = forms.ModelMultipleChoiceField(
        queryset=Keyword.objects.all(),
        widget=s2forms.ModelSelect2TagWidget(
            search_fields=['keyword__icontains'],
            attrs={
                'data-token-separators': '[","]'}),
        required=True,
        help_text=_('Please select or add 2-3 keywords separated by commas or by pressing enter.'),
        label=_('Keywords'))

    # Useful information to classify the project
    start_date = forms.DateField(
        widget=forms.TextInput(attrs={'type': 'date'}),
        required=False,
        label=_("Closest approximate start date of the project"))

    end_date = forms.DateField(
        widget=forms.TextInput(attrs={'type': 'date'}),
        required=False,
        label=_("Approximate end date of the project"))

    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.none(),
        widget=Select2MultipleWidget(),
        help_text=_("Please select the topic or field(s) of science regarding the project, multiple-choice options."),
        required=False,
        label=_("Topic"))

    # Participation information
    participationTask = forms.ModelMultipleChoiceField(
        queryset=ParticipationTask.objects.none(),
        widget=Select2MultipleWidget(),
        help_text=_("Please select the task(s) undertaken by participants."),
        required=False,
        label=_("Participation Task"))

    how_to_participate = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_("Please describe how people can get involved in the project (max 2000 characters)."),
        max_length=2000,
        label=_("How to participate"),
        required=False)

    equipment = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_(
            'Please indicate any required or suggested equipment '
            'to be used in the project (max 2000 characters).'),
        max_length=2000,
        label=_("Equipment"),
        required=False)

    # Project location
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.HiddenInput())

    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.HiddenInput(),
        required=False)

    # Contact and hosts details
    contact_person = forms.CharField(
        max_length=100,
        widget=forms.TextInput(),
        help_text=_('Please name the contact person or contact point of the project.'),
        required=False,
        label=_("Project contact point"))

    contact_person_email = forms.EmailField(
        required=False,
        widget=forms.TextInput(),
        help_text=_('Please provide the email address of the contact person or contact point.'),
        label=_("Contact point email"))

    mainOrganisation = forms.ModelChoiceField(
        queryset=Organisation.objects.all(),
        widget=s2forms.ModelSelect2Widget(
            model=Organisation,
            search_fields=['name__icontains', ]),
        help_text=_(
            "Organisation that coordinates the project. If not listed, please "
            "add it <a href=\"/new_organisation\" target=\"_blank\">here</a> "
            "before submitting the project"),
        label=_('Lead organisation'),
        required=False)

    organisation = forms.ModelMultipleChoiceField(
        queryset=Organisation.objects.all(),
        widget=s2forms.ModelSelect2MultipleWidget(
            model=Organisation,
            search_fields=['name__icontains']),
        help_text=_(
            "Other organisation(s) participating in the project. If not "
            "listed,please add it <a href=\"/new_organisation\" target=\"_blank\">here</"
            "a> before submitting the project"),
        label=_("Partnering organisations"),
        required=False)

    # Funding information
    funding_body = forms.ModelMultipleChoiceField(
        queryset=FundingBody.objects.all(),
        widget=s2forms.Select2TagWidget(
            attrs={'data-token-separators': '[","]'}
        ),
        help_text=_("Please enter the funding agencies of the project (e.g. European "
                    "Commission). Select them from the list or add your own, separated "
                    "by commas or or by pressing enter."),
        required=False,
        label=_("Funding"))

    funding_program = forms.CharField(
        max_length=500,
        widget=forms.TextInput(),
        label=_("Funding source"),
        help_text=_("Please indicate the name of the source or programme that funds or funded the project, if any."),
        required=False)

    # Images
    image1 = forms.ImageField(
        required=False,
        label=_("Image for the project’s profile thumbnail"),
        help_text=_("The image (.jpg or .png) will be resized to 600x400 pixels. "
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"),
        widget=forms.FileInput(attrs={'data-image-suffix': '1', 'data-image-width-option': 0}))

    x1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height1 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    withImage1 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    image_credit1 = forms.CharField(
        max_length=300,
        required=False,
        label=_("Provide thumbnail credit, if applicable"))

    image2 = forms.ImageField(
        required=False,
        label=_("Project logo"),
        help_text=_("The image (.jpg or .png) will be resized to 600x400 pixels. "
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"),
        widget=forms.FileInput(attrs={'data-image-suffix': '2', 'data-image-width-option': 0}))
    x2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height2 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    withImage2 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    image_credit2 = forms.CharField(
        max_length=300,
        required=False,
        label=_("Provide image credit, if applicable"))

    image3 = forms.ImageField(
        required=False,
        label=_("Image for the profile heading"),
        help_text=_("The image (.jpg or .png) will be resized to 1100x400 pixels. "
                    "Image files with dimensions that greatly differ from this size may be "
                    "drastically cropped. To learn how to avoid this, see our <a href='/"
                    "guide' target='_blank'>User Guide.</a>"),
        widget=forms.FileInput(attrs={'data-image-suffix': '3', 'data-image-width-option': 1}))
    x3 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y3 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width3 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height3 = forms.FloatField(widget=forms.HiddenInput(), required=False)
    withImage3 = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
    image_credit3 = forms.CharField(
        max_length=300,
        required=False,
        label=_("Provide heading image credit, if applicable"))

    # Others, some of them unused
    host = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={'placeholder': 'Enter the name of the institution hosting or coordinating the project'}),
        required=False)
    participatingInaContest = forms.BooleanField(
        required=False,
        label='I want to participate in the #MonthOfTheProjects and agree to be contacted via email if the'
              'project I am submitting wins the contest.'
              '<a href="/blog/2021/05/31/june-monthoftheprojects-eu-citizenscience/"> Learn more here!</a>')
    # Custom fields
    title = forms.CharField(max_length=100, required=False)
    paragraph = forms.CharField(widget=SummernoteWidget(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset here to reflect language change results
        self.fields['topic'].queryset = Topic.objects.translated_sorted_by_text()
        self.fields['participationTask'].queryset = ParticipationTask.objects.translated_sorted_by_text()

    def save(self, args, images, cFields, mainOrganisationFixed):
        pk = self.data.get('projectID', '')
        start_dateData = self.data['start_date']
        end_dateData = self.data['end_date']

        status = get_object_or_404(Status, id=self.data['status'])
        if self.data['mainOrganisation']:
            mainOrganisation = get_object_or_404(Organisation, id=self.data['mainOrganisation'])
        else:
            mainOrganisation = None

        doingAtHome = False
        if 'doingAtHome' in self.data and self.data['doingAtHome'] == 'on':
            doingAtHome = True

        participatingInaContest = False
        if 'participatingInaContest' in self.data and self.data['participatingInaContest'] == 'on':
            participatingInaContest = True

        if pk:
            project = get_object_or_404(Project, id=pk)
            if project.hidden:
                project.hidden = False
            self.updateFields(
                project,
                status,
                doingAtHome,
                mainOrganisation)
        else:
            project = self.createProject(
                status,
                doingAtHome,
                participatingInaContest,
                mainOrganisation,
                args)

        if start_dateData:
            project.start_date = start_dateData
        if end_dateData:
            project.end_date = end_dateData

        if images[0] != '/':
            project.image1 = images[0]
        if images[1] != '/':
            project.image2 = images[1]
        if images[2] != '/':
            project.image3 = images[2]

        if not pk:
            project.save()
            # Add log admin style
            log_message(project, [{'added': {}}], project.creator, ADDITION)

        project.topic.set(self.data.getlist('topic'))
        project.keywords.set(self.data.getlist('keywords'))
        project.fundingBody.set(self.data.getlist('funding_body'))
        project.participationTask.set(self.data.getlist('participationTask'))
        project.organisation.set(self.data.getlist('organisation'))
        project.save()

        return project.id

    def createProject(self, status, doingAtHome, participatingInaContest, mainOrganisation, args):
        return Project(
            creator=args.user,
            name=self.data['project_name'],
            url=self.cleaned_data['url'],
            description=self.data['description'],
            description_citizen_science_aspects=self.data['description_citizen_science_aspects'],
            latitude=self.data['latitude'],
            longitude=self.data['longitude'],
            mainOrganisation=mainOrganisation,
            author=self.data['contact_person'],
            author_email=self.data['contact_person_email'],
            status=status,
            imageCredit1=self.data['image_credit1'],
            imageCredit2=self.data['image_credit2'],
            imageCredit3=self.data['image_credit3'],
            howToParticipate=self.data['how_to_participate'],
            equipment=self.data['equipment'],
            fundingProgram=self.data['funding_program'],
            country=getCountryCode(self.data['latitude'], self.data['longitude']),
            # originUID=self.data['originUID'],
            # originURL=self.data['originURL'],
            # doingAtHome=doingAtHome,
            participatingInaContest=participatingInaContest)

    def updateFields(self, project, status, doingAtHome, mainOrganisation):
        project.name = self.data['project_name']
        project.url = self.cleaned_data['url']
        project.latitude = self.data['latitude']
        project.longitude = self.data['longitude']
        project.author = self.data['contact_person']
        project.author_email = self.data['contact_person_email']
        project.description = self.data['description']
        project.description_citizen_science_aspects = self.data['description_citizen_science_aspects']
        project.status = status
        project.imageCredit1 = self.data['image_credit1']
        project.imageCredit2 = self.data['image_credit2']
        project.imageCredit3 = self.data['image_credit3']
        project.howToParticipate = self.data['how_to_participate']
        project.doingAtHome = doingAtHome
        project.equipment = self.data['equipment']
        project.fundingProgram = self.data['funding_program']
        project.mainOrganisation = mainOrganisation
        project.country = getCountryCode(project.latitude, project.longitude)

        # If there are translations, need to improve them
        project.translatedProject.all().update(needsUpdate=True)


''' This is the form to translate projects '''


class ProjectTranslationForm(forms.Form):
    translatedDescription = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_('Please provide a <i>description</i> field translation.'),
        max_length=10000,
        label=_("Description"))

    translatedHowToParticipate = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_('Please provide a <i>how to participate</i> field translation.'),
        max_length=10000,
        label=_("How to participate"),
        required=False)

    translatedEquipment = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        help_text=_('Please provide an <i>equipment</i> field translation.'),
        max_length=10000,
        label=_("Needed equipment"),
        required=False)

    def save(self, args):
        project = Project.objects.get(id=self.data.get('projectId'))
        translation = project.translatedProject.filter(inLanguage=self.data.get('languageId')).first()
        if translation:
            TranslatedProject.objects.filter(id=translation.id).delete()
        t1 = TranslatedProject(
            inLanguage=self.data.get('languageId'),
            translatedDescription=self.data.get('translatedDescription'),
            translatedHowToParticipate=self.data.get('translatedHowToParticipate'),
            translatedEquipment=self.data.get('translatedEquipment'),
            needsUpdate=False,
            creator=args.user,
        )
        t1.save()
        project.translatedProject.add(t1)
        project.save()


class CustomFieldForm(forms.Form):
    title = forms.CharField(max_length=100, required=False)
    paragraph = forms.CharField(widget=SummernoteWidget(), required=False)


class ProjectPermissionForm(forms.Form):
    selectedUsers = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersCollection = forms.CharField(widget=forms.HiddenInput(), required=False, initial=())
    usersAllowed = forms.MultipleChoiceField(
        choices=(),
        widget=Select2MultipleWidget,
        required=False,
        label=_("Give additional users permission to edit"))


class InviteProjectForm(forms.Form):
    project_id = forms.IntegerField(widget=forms.HiddenInput)
    email = forms.EmailField(label=_("Editor's email"), required=False,
                             help_text=_("You can invite an editor to this project. Enter their email address here to "
                                         "send the invitation. Editors are authorized to change all registration "
                                         "information. Therefore, be careful when assigning this role to someone."
                                         ))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        project_id = cleaned_data.get('project_id')
        # email is required, but final user don't want "*" (from crispy) only in this field!
        if email:
            try:
                user = USER.objects.get(email=email)

                if user.pk == self.data['current_user'].pk:
                    self.add_error('email', _("You can't invite yourself"))

                if Project.objects.filter(creator=user, pk=project_id).exists():
                    self.add_error('email', _("You can't invite project creator"))

                if ProjectPermission.objects.invite_accepted(project_id, user):
                    self.add_error('email', _('User already accepted invite for this project'))

                cleaned_data['user'] = user

            except USER.DoesNotExist:
                cleaned_data['user'] = None
        else:
            self.add_error('email', self.fields['email'].default_error_messages['required'])
        return cleaned_data

    def save(self):
        if self.cleaned_data['user'] is not None:
            # Create a pending permission when user exists.
            project = Project.objects.get(pk=self.cleaned_data['project_id'])
            ProjectPermission.objects.get_or_create(user=self.cleaned_data['user'], project=project)
        else:
            # Create a task to be executed after user activation.
            ActivationTask.objects.update_or_create(
                email=self.cleaned_data['email'],
                defaults={
                    'task_module': 'projects.views', 'task_name': 'project_invitation',
                    'task_kwargs': {'project_id': self.cleaned_data['project_id']},
                    'task_description': _('Grants an unregistered user permission to edit a project')
                }
            )
