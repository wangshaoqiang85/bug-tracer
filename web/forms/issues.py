from django import forms
from django.core.exceptions import ValidationError
from web.forms.bootstrap import BootstrapForm
from web.forms.widgets import PriorityColorSelect
from web.models import Issues,IssuesType, Module, ProjectUser, ProjectInvite


class IssuesModelForm(BootstrapForm, forms.ModelForm):

    class Meta:
        model = Issues
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']

        widgets = {
            'assign': forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            'attention': forms.SelectMultiple(   # SelectMultiple 是多选
                attrs={
                    'class': "selectpicker",
                    "data-live-search": "true",
                    "data-actions-box": "true"
                }),
            "parent": forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            'priority': PriorityColorSelect(attrs={'class': "selectpicker"}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

        # 1、获取所有问题类型
        type_list = IssuesType.objects.filter(project=request.tracer.project).values_list('id', 'title')
        self.fields['issues_type'].choices = type_list

        # 2、获取所有的模块分类
        module_list = [('', '空')]
        module_object = Module.objects.filter(project=request.tracer.project).values_list('id', 'title')
        module_list.extend(module_object)
        self.fields['module'].choices = module_list

        # 3、获取指派者和关注者
        assign_list = [(request.tracer.project.creator.id, request.tracer.project.creator.username)]
        other_list = ProjectUser.objects.filter(project=request.tracer.project).values_list('user_id', 'user__username')
        assign_list.extend(other_list)
        self.fields['assign'].choices = [('', '不指派'), ] + assign_list
        # print(self.fields['assign'].choices)
        self.fields['attention'].choices = assign_list

        # 4、当前项目中已经创建的问题
        parent_list = [('', '没有父问题')]
        parent_object = Issues.objects.filter(project=request.tracer.project).values_list('id', 'subject')
        parent_list.extend(parent_object)
        self.fields['parent'].choices = parent_list

    def clean_subject(self):
        subject = self.cleaned_data['subject']

        exists = Issues.objects.filter(subject=subject).exists()
        if exists:
            raise ValidationError('当前项目中该问题主题已经存在！')

        return subject


class InviteModelForm(BootstrapForm, forms.ModelForm):
    class Meta:
        model = ProjectInvite
        fields = ['period', 'count']




