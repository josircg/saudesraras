from PIL import Image
from django_countries.serializer_fields import CountryField
from organisations.models import Organisation, OrganisationType
from rest_framework import serializers

from utilities.file import save_image_with_path


class OrganisationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationType
        fields = '__all__'


class OrganisationSerializer(serializers.ModelSerializer):
    orgType = OrganisationTypeSerializer(many=False)
    country = CountryField(required=False)

    class Meta:
        model = Organisation
        fields = ['id', 'name', 'url', 'description', 'orgType', 'logo', 'contactPoint', 'contactPointEmail',
                  'latitude', 'longitude', 'country']


class OrganisationSerializerCreateUpdate(serializers.ModelSerializer):
    orgType = serializers.PrimaryKeyRelatedField(queryset=OrganisationType.objects.all(), many=False)
    country = CountryField(required=False)

    class Meta:
        model = Organisation
        fields = ['id', 'name', 'url', 'description', 'orgType', 'logo', 'contactPoint', 'contactPointEmail',
                  'latitude', 'longitude', 'country']

    def save(self, args, **kwargs):
        logo = self.validated_data.get('logo')
        if logo:
            image = Image.open(logo)
            logo = save_image_with_path(image, logo.name)

        moreItems = [('creator', args.user), ('logo', logo)]

        data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items()) + list(moreItems)
        )

        self.instance = self.create(data)

        return "success"
