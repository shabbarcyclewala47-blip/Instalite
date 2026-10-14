from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect


urlpatterns = [
    # Redirect the main website to the InstaLite home page
    path('', lambda request: redirect('/index/'), name='home'),

    path('admin/', admin.site.urls),

    # InstaLite Home
    path('index/', include('index.urls')),

    # Posts
    path('posts/', include('posts.urls')),

    # Accounts
    path('accounts/', include('accounts.urls')),

    # Insights
    path('insights/', include('insights.urls')),

    # Portfolio
    path(
        'portfolio/',
        lambda request: render(request, 'shabbarportfolio.html'),
        name='portfolio'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

