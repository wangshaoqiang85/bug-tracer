from django import forms
from django.core.exceptions import ValidationError
from web.models import FileRepository
from web.forms.bootstrap import BootstrapForm

from utils.tencent.cos import check_file


class FolderModelForm(BootstrapForm, forms.ModelForm):
    class Meta:
        model = FileRepository
        fields = ['name']

    def __init__(self, request, parent_object=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_object = parent_object

    def clean_name(self):
        """当前目录下不能存在重名的文件夹"""
        name = self.cleaned_data['name']

        queryset = FileRepository.objects.filter(file_type=2, name=name, project=self.request.tracer.project)
        if self.parent_object:
            exists = queryset.filter(parent=self.parent_object).exists()
        else:
            exists = queryset.filter(parent__isnull=True).exists()

        if exists:
            raise ValidationError('文件夹已经存在')

        return name


class FileModelForm(forms.ModelForm):
    etag = forms.CharField(label='腾讯cos的ETag')

    class Meta:
        model = FileRepository
        fields = ['name', 'key', 'file_size', 'file_path', 'parent']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        return 'https://{}'.format(self.cleaned_data['file_path'])

    def clean(self):
        key = self.cleaned_data['key']
        size = self.cleaned_data['file_size']
        etag = self.cleaned_data['etag']
        if not key and not etag:
            return self.cleaned_data

        # 向COS校验文件是否合法
        from qcloud_cos.cos_exception import CosServiceError
        try:
            response = check_file(self.request.tracer.project.bucket, self.request.tracer.project.region, key)
        except CosServiceError as e:
            self.add_error('key', '文件名不存在')
            return self.cleaned_data

        cos_etag = response.get('ETag')
        if etag != cos_etag:
            self.add_error('ETag', 'ETag错误')

        cos_length = response.get('Content-Length')
        if int(cos_length) != size:
            self.add_error('file_size', '文件大小错误')

        return self.cleaned_data

