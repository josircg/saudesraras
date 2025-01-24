from django.urls import path, include
from django.conf.urls import url
from . import views

urlpatterns = [
    path('newProject', views.newProject, name='newProject'),
    path('editProject/<int:pk>', views.editProject, name='editProject'),
    path('saveProjectAjax', views.saveProjectAjax, name='saveProjectAjax'),
    path('projects', views.projects, name='projects'),
    path('projects_stats', views.projects_stats, name='projects_stats'),
    path('getProjectTranslation/', views.getProjectTranslation, name='getProjectTranslation'),
    path('submitProjectTranslation/', views.submitProjectTranslation, name='submitProjectTransalation'),
    path('project/<int:pk>', views.project, name='project'),
    path('approve_project/<int:pk>/<int:status>', views.approve_project, name='approve_project'),
    path('deleteProject/<int:pk>', views.deleteProject, name='deleteProject'),
    path('translateProject/<int:pk>', views.translateProject, name='translateProject'),
    path('clearfilters/', views.clearFilters, name='clearfilters'),
    path('setHidden/', views.setHidden, name='setHidden'),
    path('setFeatured/', views.setFeatured, name='setFeatured'),
    path('setFollowedProject/', views.setFollowedProject, name='setFollowedProject'),
    path('allowUser/', views.allowUser, name='allowUser'),
    path('project_review/<int:pk>', views.project_review, name='project_review'),
    url(r'^api/', include('projects.api.urls')),
    path('downloadProjects', views.downloadProjects, name='downloadProjects'),
    path('test_visao/', views.test_visao, name='test_visao'),
    path('project_invite/', views.project_invite, name='project_invite'),
    path('project_invitation/<int:project_id>/', views.project_invitation, name='project_invitation'),
    path('project_permissions/<int:project_id>/', views.project_permission_list, name='project_permissions'),
    path('delete_project_permission/<int:permission_id>/', views.delete_project_permission,
         name='delete_project_permission'),
    path('delete_non_registered_user_invitation/<int:task_id>/', views.delete_non_registered_user_invitation,
         name='delete_non_registered_user_invitation'),
]
