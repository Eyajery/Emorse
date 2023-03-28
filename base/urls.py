from django.urls import path
from . import views

urlpatterns = [
    path('', views.first ,name='first'),
    path('home/', views.home ,name='home'),
    path('homes/', views.homes ,name='homes'),
    path('room_t/', views.room_t),
     path('room_s/', views.room_s),
    path('get_token/', views.getToken),

    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('student/', views.student, name='student'),
    path('detect-emotion/', views.emotion_detection, name='detect_emotion'),
    path('dashboard_t/', views.dashboard_t, name='dashboard_t'),
    path('dashboard_s/', views.dashboard_s, name='dashboard_s'),
    path('lobby/', views.lobby, name='lobby'),

]