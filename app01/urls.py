from django.conf.urls import url
from app01.views import *

app_name = 'app01'
urlpatterns = [
    url(r'^register/', register, name="register"),
    url(r'^send_mes', send_mes, name="send_mes"),  # 测试前端Vue能否发送手机给后台
    url(r'^sendmes/', sendMes, name="sendmes"),  # 测试短信API
]