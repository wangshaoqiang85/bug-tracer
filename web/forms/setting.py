from django import forms
from django.core.exceptions import ValidationError

from utils import encrypt
from web.models import Wiki
from web.forms.bootstrap import BootstrapForm


class ChangePasswordForm(forms.Form):
    password = forms.CharField(label='原密码')
    new_password = forms.CharField(label='新密码')
    new_confirm_password = forms.CharField(label='确认密码')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        # 密码加密
        pwd = encrypt.md5(pwd)
        user_pwd = self.request.tracer.user.password
        # 验证原密码是否输入正确
        if pwd != user_pwd:
            raise ValidationError('原密码错误！')

        return pwd

    def clean_new_password(self):
        pwd = self.cleaned_data['new_password']
        # 新密码加密
        pwd = encrypt.md5(pwd)
        return pwd

    def clean_new_confirm_password(self):
        new_password = self.cleaned_data['new_password']
        new_confirm_password = self.cleaned_data['new_confirm_password']
        # 重复密码也需要加密处理
        cpwd = encrypt.md5(new_confirm_password)
        if new_password != cpwd:
            raise ValidationError('两次密码输入不一致')
        return new_confirm_password




