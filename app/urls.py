from django.urls import path, include
from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('private_events/', views.private_events, name='private_events'),
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/create/', views.create_event, name='create_event'),
    path('user/<int:pk>/', views.user_detail, name='user_detail'),
    path('user/edit/', views.edit_profile, name='edit_profile'),
    path('event/<int:pk>/participation/', views.participation, name='participation'),
    path('event/<int:pk>/comment/', views.comment, name='comment'),
    path('event/<int:pk>/rate', views.rate_event, name='rate_event'),
    path('user/<int:pk>/follow/', views.follow_user, name='follow_user'),
    path('event/<int:event_id>/invite_users/', views.invite_users, name='invite_users')
]

