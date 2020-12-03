from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django import forms
from django_redis import get_redis_connection
from utils.tencent.sms import send_sms_single
from utils import encrypt
from web.models import UserInfo
from .bootstrap import BootstrapForm
from web import tasks

# 注册表单验证
class RegisterModelForm(BootstrapForm, forms.ModelForm):
    password = forms.CharField(label='密码',
                               min_length=8,
                               max_length=16,
                               error_messages={
                                   'min_length': '密码长度不能小于8个字符',
                                   'max_length': '密码长度不能大于16个字符'
                               },
                               widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput)

    # validators传入列表，可以加入多个验证
    # RegexValidator是正则表达匹配
    mobile_phone = forms.CharField(label="手机号", validators=[RegexValidator(r'^1[3|4|5|6|7|8|9]\d{9}$', '请输入正确的手机号'), ])

    # 验证码
    code = forms.CharField(label='邮箱验证码')
    # 使用widget自定义属性
    # code = forms.CharField(label='验证码',widget=forms.TextInput(attrs={'size':'40'}))

    class Meta:
        model = UserInfo   # 需要校验的模型类
        # fields可以控制展示顺序
        # fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']
        fields = ['username', 'mobile_phone', 'password', 'confirm_password', 'email']

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = UserInfo.objects.filter(username=username).exists()
        if exists:
            raise ValidationError('用户名已经存在')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        exists = UserInfo.objects.filter(email=email).exists()
        if exists:
            raise ValidationError('邮箱已经注册')
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        # 密码加密
        pwd = encrypt.md5(pwd)
        return pwd

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        # 重复密码也需要加密处理
        cpwd = encrypt.md5(confirm_password)
        if password != cpwd:
            raise ValidationError('两次密码输入不一致')
        return confirm_password

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError('手机号已经注册')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']

        # mobile_phone = self.cleaned_data['mobile_phone']
        email = self.cleaned_data.get('email')
        if not email:
            return code

        conn = get_redis_connection()
        redis_code = conn.get(email)
        if not redis_code:
            raise ValidationError('验证码无效或未发送，请重新发送')
        redis_code = redis_code.decode('utf-8')  # redis中的数据是字节类型，需要解码
        # print(redis_code)
        if redis_code.strip() != code.strip():
            raise ValidationError('验证码错误，请重新输入')

        return code


class SendEmailForm(forms.Form):
    email = forms.EmailField(label="邮箱")

    # 重写初始化方法，获取request中的tpl(短信模板）参数
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_email(self):
        '''手机号校验的钩子'''
        email = self.cleaned_data['email']

        # 校验短信模板是否有问题（登录验证码和注册验证码使用两套短信模板）
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not template_id:
            raise ValidationError("短信模板错误")

        # 校验数据库中是否已经存在手机号
        exist = UserInfo.objects.filter(email=email).exists()
        # 如果是登录验证的模板，要判断手机号不存在的情况
        if tpl == 'login':
            if not exist:
                raise ValidationError('邮箱账号不存在')
        # 如果是注册验证的模板，要判断手机号存在的情况
        else:
            if exist:
                raise ValidationError('邮箱账号已存在')

        # 发送短信
        import random
        code = str(random.randrange(100000, 999999))
        # sms = send_sms_single(mobile=mobile_phone, code=code, template_id=template_id)
        # import json
        # sms = json.loads(sms)
        # if sms['code'] != "0":
        #     raise ValidationError('短信发送失败，{}'.format(sms['msg']))
        # print(email)
        tasks.send_verify_email.delay(email, code)

        # 验证码写入redis
        conn = get_redis_connection()  # 默认是default
        # print(code)
        conn.set(email, code, ex=300)

        return email


# 后台发送的手机号和短信模板校验
class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label="手机号", validators=[RegexValidator(r'^1[3|4|5|6|7|8|9]\d{9}$', '请输入正确的手机号'), ])

    # 重写初始化方法，获取request中的tpl(短信模板）参数
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_mobile_phone(self):
        '''手机号校验的钩子'''
        mobile_phone = self.cleaned_data['mobile_phone']

        # 校验短信模板是否有问题（登录验证码和注册验证码使用两套短信模板）
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not template_id:
            raise ValidationError("短信模板错误")

        # 校验数据库中是否已经存在手机号
        exist = UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        # 如果是登录验证的模板，要判断手机号不存在的情况
        if tpl == 'login':
            if not exist:
                raise ValidationError('手机号不存在')
        # 如果是注册验证的模板，要判断手机号存在的情况
        else:
            if exist:
                raise ValidationError('手机号已存在')

        # 发送短信
        import random
        code = str(random.randrange(1000, 9999))
        # sms = send_sms_single(mobile=mobile_phone, code=code, template_id=template_id)
        # import json
        # sms = json.loads(sms)
        # if sms['code'] != "0":
        #     raise ValidationError('短信发送失败，{}'.format(sms['msg']))

        # 验证码写入redis
        conn = get_redis_connection()  # 默认是default
        code = template_id + code
        print(code)
        conn.set(mobile_phone, code, ex=60)

        return mobile_phone


# 短信登录验证
class LoginSmsForm(BootstrapForm, forms.Form):
    mobile_phone = forms.CharField(
        label="手机号",
        validators=[RegexValidator(r'^1[3|4|5|6|7|8|9]\d{9}$', '请输入正确的手机号'),]
    )

    code = forms.CharField(label='验证码')

    # 字段校验函数
    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exists:
            raise ValidationError('手机号不存在')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']

        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code

        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)

        if not redis_code:
            raise ValidationError('验证码无效或未发送，请重新发送')
        redis_code = redis_code.decode('utf-8')  # redis中的数据是字节类型，需要解码
        print(redis_code)
        if redis_code.strip() != code.strip():
            raise ValidationError('验证码错误，请重新输入')

        return code


# 用户名和密码登录验证
class LoginForm(BootstrapForm, forms.Form):
    username = forms.CharField(label='邮箱或手机号')
    password = forms.CharField(label='密码', widget=forms.PasswordInput(render_value=True))
    code = forms.CharField(label='图片验证码')

    # 重写初始化方法，获取request中的session中的图片验证码
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        pwd = encrypt.md5(pwd)
        return pwd

    def clean_code(self):
        code = self.cleaned_data['code']

        # 去session获取图片验证码信息
        img_code = self.request.session.get('image_code')
        if not img_code:
            raise ValidationError('验证码失效, 请刷新重试')

        if code.strip().upper() != img_code.strip().upper():
            raise ValidationError('验证码输入错误')

        return code

