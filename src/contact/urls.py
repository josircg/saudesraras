from django.urls import path

from . import views

urlpatterns = [
    path('contact/', views.contactView, name='contact'),
    path('count/<int:pk>', views.countView, name='count'),
    path('import_subscriber_csv/', views.import_csv, name='import_subscriber_csv'),
    path('submitter_contact/<slug:group>/<int:pk>', views.submitterContactView, name='submitter_contact'),
    path('subscribe/', views.subscribeView, name='subscribe'),
    path('confirm_email/<str:token>/<int:id>', views.confirm_email, name='confirm_email'),
    path('unsubscribe/<str:token>/<int:id>', views.unsubscribe, name='unsubscribe'),
    path('test_newsletter/<int:pk>', views.test_newsletter, name='test_newsletter'),
    path('render_newsletter/<int:pk>', views.render_newsletter, name='render_newsletter'),
    path('newsletter/<int:pk>', views.newsletter, name='newsletter'),
    path('newsletters', views.NewsletterList.as_view(), name='newsletters'),
    path('load_image/<str:image_name>', views.load_image, name='load_image'),
    path('forum_proposal/', views.NewForumProposal.as_view(), name='forum_proposal'),
]
