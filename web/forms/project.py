from django import forms
from django.core.exceptions import ValidationError
from web.models import *
from .bootstrap import BootstrapForm
from web.forms.widgets import ColorRadioSelect


class ProjectModelForm(BootstrapForm, forms.ModelForm):
    bootstrap_class_exclude = ['color']
    # desc = forms.CharField(label='项目描述', widget=forms.Textarea(attrs={'size': 123}))

    class Meta:
        model = Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            # 默认是Select类型,修改成RadioSelect
            # 'color': forms.Select
            # 'color': forms.RadioSelect,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        '''项目名称校验'''
        name = self.cleaned_data['name']
        # 1、判断当前用户是否已经创建过该项目
        exists = Project.objects.filter(name=name, creator=self.request.tracer.user).exists()
        if exists:
            raise ValidationError('项目名称已存在')

        # 2、当前用户的是否还有空间额度创建项目
        # 获取当前用户额度
        cur_num = self.request.tracer.price_policy.project_num
        # 当前用户已经创建的项目数量
        count = Project.objects.filter(creator=self.request.tracer.user).count()
        if count >= cur_num:
            raise ValidationError('项目个数超限，请购买套餐')

        return name





