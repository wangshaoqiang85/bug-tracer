from django.shortcuts import render
from django.core.validators import RegexValidator
from django import forms
from app01.models import UserInfo
from django.conf import settings
import random
from utils.tencent.sms import send_sms_single

# 测试短信api是否可用
def sendMes(request):
    """ 发送短信
        ?tpl=login  -> 00
        ?tpl=register -> 11
    """
    template_id = "11"
    # tpl = request.GET.get('tpl')
    # template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    # if not template_id:
    #     return HttpResponse("模板不存在")
    code = str(random.randrange(1000, 9999))
    res = send_sms_single(mobile='17864195254', code=code, template_id=template_id)
    import json
    res = json.loads(res)  # 将json数据解码成字典类型
    if res['code'] == "0":
        print(res)
        return HttpResponse('验证码发送成功')
    else:
        return HttpResponse(res['msg'])

# 表单验证
class RegisterModelForm(forms.ModelForm):
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput)

    # validators传入列表，可以加入多个验证
    # RegexValidator是正则表达匹配
    mobile_phone = forms.CharField(label="手机号", validators=[RegexValidator(r'^1[3|4|5|6|7|8|9]\d{9}$', '请输入正确的手机号'), ])
    code = forms.CharField(label='验证码')

    class Meta:
        model = UserInfo
        # fields可以控制展示顺序
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name,field in self.fields.items():
            # 给表单添加样式
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入{}'.format(field.label)

def register(request):
    form = RegisterModelForm()
    return render(request, 'app01/register_01.html',{'form':form})

# def register(request):
#     if request.method == 'GET':
#         return render(request, 'app01/register.html')
#     if request.method == 'POST':
#         pass

from django.http import JsonResponse, HttpResponse
def send_mes(request):
    if request.method=='POST':
        phone = request.POST.get('phone')
        if not phone:
            print('手机号不存在')
        data={"name":"kang","age":18}
        return JsonResponse(data, safe=False)
    else:
        print("get请求")
        data = {"name": "kang", "age": 99}
        return JsonResponse(data, safe=False)



