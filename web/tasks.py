from django.core.mail import send_mail
from celery import task
from time import sleep
from bug_tracer.settings import DEFAULT_FROM_EMAIL


@task
def send_verify_email(email, code):
    subject = "bug追踪管理系统"
    message = "尊敬的用户您好！您的验证码为 "+code+", 验证码5分钟内有效"
    # sleep(10)
    try:
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [email])
    except:
        pass
