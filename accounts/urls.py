from django.urls import path
from . import views

urlpatterns = [
    path('register/',views.register,name='register'),
     path('login/',views.loggedin,name='loggedin'),
    path('logout/', views.loggedout, name='logout'),
    
    path('forgotpassword/',views.forgotpassword,name='forgotpassword'),
    path('activate/''<uid>/''<token>/',views.activate,name='activate'),
    path('resetpassword/',views.resetpassword,name='resetpassword'),
]