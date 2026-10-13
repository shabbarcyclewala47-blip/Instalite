from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


urlpatterns = [

    path('admin/', admin.site.urls),

    # InstaLite Home
    path(
        'index/',
        include('index.urls')
    ),

    # Posts
    path(
        'posts/',
        include('posts.urls')
    ),

    # Accounts
    path(
        'accounts/',
        include('accounts.urls')
    ),

    path(
        'insights/',
        include('insights.urls')
    ),
    path('portfolio/', lambda request: render(
        request, 'shabbarportfolio.html'
    ), name='portfolio'),
  
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )