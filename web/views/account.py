"""短信，注册，登录，注销"""

from django.shortcuts import render,HttpResponse,redirect,reverse
from django.http import JsonResponse
from django.db.models import Q
from web.forms.account import *
from web.models import PricePolicy,Transaction
import uuid
import datetime
from django.contrib.auth.models import User

def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        request.session.flush()
        return render(request, 'web/register.html', {'form': form})
    if request.method == 'POST':
        # print(request.POST)
        form = RegisterModelForm(data=request.POST)
        if form.is_valid():
            # todo 删除redis中的验证码，避免重读使用验证码登录

            # 验证通过，写入数据库
            # form.save()

            # 获取新用户的信息
            instance = form.save()

            # todo 给新用户添加免费版的交易记录,免费版的也可以不用创建
            policy_object = PricePolicy.objects.filter(category=1, title='个人免费版').first()
            Transaction.objects.create(
                status=2,
                order=str(uuid.uuid4()),
                user=instance,
                price_policy=policy_object,
                count=0,
                price=0,
                start_datetime=datetime.datetime.now()
            )

            return JsonResponse({'status': True, 'data': '/login/'})
        # 验证失败
        return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):
    # print(request.GET)
    # form = SendSmsForm(request, data=request.GET)
    form = SendEmailForm(request, data=request.GET)

    # 如果校验成功（校验部分在SendSmsForm类中定义）
    if form.is_valid():
        return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'error': form.errors})


def login_sms(request):
    if request.method == 'GET':
        form = LoginSmsForm()
        return render(request, 'web/login_sms.html', {'form': form})

    if request.method == 'POST':

        form = LoginSmsForm(request.POST)

        if form.is_valid():
            # todo 删除redis中的验证码，避免重读使用验证码登录

            mobile_phone = form.cleaned_data['mobile_phone']

            # todo 用户信息放入session
            user_object = UserInfo.objects.get(mobile_phone=mobile_phone)
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60 * 60 * 24 * 7)  # 设置保存一周
            # request.session['username'] = user_object.username

            return JsonResponse({'status': True, 'data': '/index/'})

        return JsonResponse({'status': False, 'error': form.errors})

# 用户名和密码登录
def login(request):
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'web/login.html', {'form': form})

    if request.method == 'POST':
        # 传递request，获取session中的图片验证码信息
        form = LoginForm(request, data=request.POST)
        # 表单验证通过
        if form.is_valid():
            username = form.cleaned_data['username']
            pwd = form.cleaned_data['password']

            # user_object = UserInfo.objects.filter(username=username, password=pwd).first()
            user_object = UserInfo.objects.filter(Q(email=username)
                                                  | Q(mobile_phone=username)).filter(password=pwd).first()
            if user_object:
                # 用户id写入session
                request.session['user_id'] = user_object.id
                request.session.set_expiry(60 * 60 * 24 * 7)
                # 如果存在，跳转到首页
                return redirect(reverse('web:index'))
            # 如果不存在，返回登录页
            form.add_error('username', '用户名或密码错误')
            return render(request, 'web/login.html', {'form': form})

        # 表单验证失败
        return render(request, 'web/login.html', {'form': form})


# 生成图片验证码
def image_code(request):
    from utils.img_code.image_code import check_code
    from io import BytesIO

    image_object, code = check_code()

    request.session['image_code'] = code
    request.session.set_expiry(60)   # 主动设置session的过期时间为60s

    # 把图片的内容写到内存 stream
    stream = BytesIO()
    image_object.save(stream, 'png')

    return HttpResponse(stream.getvalue())

    # 如果验证码图片不写入内存，可以这样，
    # 但是多个用户使用时，验证码文件名混混乱
    # with open('code.png', 'wb') as f:
    #     image_object.save(f, format='png')
    # with open('code.png', 'rb') as f:
    #     data = f.read()
    # return HttpResponse(data)


def logout(request):
    request.session.flush()

    return redirect(reverse('web:index'))






