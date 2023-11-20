from django.db.models import Q
from django.http import Http404
from projects.api.serializers import ProjectSerializer, ProjectSerializerCreateUpdate, StatusSerializer
from projects.api.serializers import ProjectTranslateSerializer, ProjectTranslateCreateSerializer
from projects.api.serializers import TopicSerializer, ParticipationTaskSerializer
from projects.models import Project, Status, Topic, ParticipationTask
from projects.models import TranslatedProject
from projects.views import setProjectApproved, setProjectHidden, setProjectFeatured, followProject, \
    has_permission_to_edit_project
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST)
from rest_framework.views import APIView


class AdminPermissionsClass(BasePermission):
    def has_permission(self, request, view):
        METHODS_WITH_PERMISSION = ["DELETE", "PUT", "POST"]
        if request.method in METHODS_WITH_PERMISSION:
            return request.user.is_staff
        return True


class StatusViewSet(viewsets.ModelViewSet):
    permission_classes = (AdminPermissionsClass,)
    serializer_class = StatusSerializer
    http_method_names = ['get']
    queryset = Status.objects.all()


class TopicViewSet(viewsets.ModelViewSet):
    permission_classes = (AdminPermissionsClass,)
    serializer_class = TopicSerializer
    http_method_names = ['get']
    queryset = Topic.objects.all()


class ParticipationTaskViewSet(viewsets.ModelViewSet):
    permission_classes = (AdminPermissionsClass,)
    serializer_class = ParticipationTaskSerializer
    http_method_names = ['get']
    queryset = ParticipationTask.objects.all()


class ProjectList(APIView):

    def applyFilters(self, request, projects):
        approvedProjects = Project.objects.filter(approved=True).values_list('pk', flat=True)

        keywords = request.query_params.get('keywords', None)
        if keywords is not None:
            projects = projects.filter(
                Q(name__icontains=keywords) |
                Q(keywords__keyword__icontains=keywords)).distinct()

        topic = request.query_params.get('topic', None)
        if topic is not None:
            projects = projects.filter(topic=topic)

        status = request.query_params.get('status', None)
        if status is not None:
            projects = projects.filter(status=status)

        country = request.query_params.get('country', None)
        if country:
            projects = projects.filter(
                Q(mainOrganisation__country=country) | Q(country=country) | Q(organisation__country=country)
            ).distinct()

        doingAtHome = request.query_params.get('doingAtHome', None)
        if doingAtHome is not None:
            doingAtHome = True if (doingAtHome == "true" or doingAtHome == '1') else False
            projects = projects.filter(doingAtHome=doingAtHome)

        if request.GET.get('approvedCheck'):
            if request.GET['approvedCheck'] == 'On':
                projects = projects.filter(id__in=approvedProjects)
            if request.GET['approvedCheck'] == 'Off':
                projects = projects.exclude(id__in=approvedProjects)
            if request.GET['approvedCheck'] == 'All':
                projects = projects
        else:
            projects = projects.filter(id__in=approvedProjects)

        return projects

    def get(self, request, format=None):
        '''
        Return a list of projects.
        '''
        projects = Project.objects.all()
        projects = self.applyFilters(request, projects)
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)


class PermissionClass(BasePermission):
    def has_permission(self, request, view):
        METHODS_WITH_PERMISSION = ["DELETE", "PUT", "POST"]
        if request.method in METHODS_WITH_PERMISSION:
            return request.user and request.user.is_active
        return True


class ProjectDetail(APIView):
    permission_classes = (PermissionClass,)

    def get_object(self, pk):
        try:
            return Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        '''
        Return a project by id.
        '''
        project = self.get_object(pk)
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk, format=None):
        project = self.get_object(pk)
        if has_permission_to_edit_project(project, request.user):
            serializer = ProjectSerializerCreateUpdate(project, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.update(project, serializer.validated_data, request.data)
                serializerReturn = ProjectSerializer(
                    Project.objects.get(pk=serializer.data.get('id')), context={'request': request})
                return Response(serializerReturn.data)
        else:
            return Response({"This user can't update this project"}, status=HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ProjectCreate(APIView):
    permission_classes = (PermissionClass,)

    def post(self, request, format=None):
        '''
        Create a project.
        '''
        serializer = ProjectSerializerCreateUpdate(data=request.data)
        if serializer.is_valid():
            serializer.save(request)
            serializerReturn = ProjectSerializer(
                Project.objects.get(pk=serializer.data.get('id')), context={'request': request})
            return Response(serializerReturn.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ProjectTranslate(APIView):
    permission_classes = (PermissionClass,)

    def post(self, request, pk, format=None):
        '''
        Translate a project
        '''
        print(pk)
        serializer = ProjectTranslateCreateSerializer(data=request.data)
        if serializer.is_valid():
            translationId = serializer.save(request, pk)
            serializerReturn = ProjectTranslateSerializer(
                TranslatedProject.objects.get(id=translationId), context={'request': request})
            return Response(serializerReturn.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([AdminPermissionsClass])
def approved_project(request, pk):
    approved = request.data.get('value')
    setProjectApproved(request.user, pk, approved)
    return Response(status=HTTP_204_NO_CONTENT)


@api_view(['PUT'])
@permission_classes([AdminPermissionsClass])
def hidden_project(request, pk):
    hidden = request.data.get('value')
    setProjectHidden(pk, hidden)
    return Response(status=HTTP_204_NO_CONTENT)


@api_view(['PUT'])
@permission_classes([AdminPermissionsClass])
def set_featured_project(request, pk):
    featured = request.data.get('value')
    setProjectFeatured(pk, featured)
    return Response(status=HTTP_204_NO_CONTENT)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def follow_project(request, pk):
    userId = request.user.id
    follow = request.data.get('value')
    followProject(pk, userId, follow)
    return Response(status=HTTP_204_NO_CONTENT)
