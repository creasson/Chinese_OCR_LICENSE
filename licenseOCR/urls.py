"""licenseOCR URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.shortcuts import render
from . import upload_view
from . import baidu_ocr_view
from . import east_view
from . import ocr_view
from . import licenseocr_view

def index(request):
    return render(request, 'index.html', None)

def baidu_ocr(request):
    return render(request, 'baidu_ocr.html',
                  context={'imgpath': "static/standard_images/企业法人营业执照2.png"})

def ocr(request):
    return render(request, 'ocr.html',
                  context={'imgpath': "static/standard_images/企业法人营业执照2.png"})

def license_ocr(request):
    return render(request, 'license_ocr.html',
                  context={'imgpath': "static/standard_images/企业法人营业执照2.png"})

urlpatterns = [
    # 网页请求
    url(r'^$', index),
    url(r'^baidu_ocr$', baidu_ocr),
    url(r'^ocr$', ocr),
    url(r'^license_ocr$', license_ocr),

    # 后台服务请求
    url(r'^upload$', upload_view.upload),
    url(r'^baidu_ocr_image$', baidu_ocr_view.ocr_image),
    url(r'^east_image$', east_view.east_image),
    url(r'^ocr_image$', ocr_view.http_ocr_image),
    url(r'^license_image$', licenseocr_view.http_ocr_image),
]