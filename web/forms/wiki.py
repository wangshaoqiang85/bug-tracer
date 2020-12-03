from django.forms import ModelForm
from django.core.exceptions import ValidationError
from web.models import Wiki
from web.forms.bootstrap import BootstrapForm


class WikiAddModelForm(BootstrapForm, ModelForm):

    class Meta:
        model = Wiki
        exclude = ['project', 'depth']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, ** kwargs)
        self.request = request
        # 找到想要的字段绑定显示的数据重置

        total_list = [('', '请选择')]
        data_list = Wiki.objects.filter(project=request.tracer.project).values_list('id', 'title')

        total_list.extend(data_list)
        self.fields['parent'].choices = total_list

    # def clean_title(self):
    #     title = self.cleaned_data['title']
    #
    #     exists = Wiki.objects.filter(project=self.request.tracer.project, title=title).exists()
    #     if exists:
    #         raise ValidationError('当前项目文件名已经存在')

        # return title



