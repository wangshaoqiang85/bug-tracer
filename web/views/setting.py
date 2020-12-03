from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse,JsonResponse

from web.forms.setting import ChangePasswordForm
from web.models import Project
from utils.tencent.cos import delete_bucket_files


def setting(request, project_id):
    return render(request, 'web/setting.html')


def setting_delete(request, project_id):
    '''删除项目'''

    if request.method == 'GET':
        return render(request, 'web/setting_delete.html')

    project_name = request.POST.get('project_name')
    if not project_name or project_name != request.tracer.project.name:
        return render(request, 'web/setting_delete.html', {'error': '项目名错误！'})

    # 判断是否是项目创建者，只有创建者可以删除项目
    if request.tracer.user != request.tracer.project.creator:
        return render(request, 'web/setting_delete.html', {'error': '只有创建者可以删除项目！'})

    # todo 1、删除cos桶 （需要先清空桶）
    #   - 删除桶中的所有文件（找到桶中所有的文件并删除）
    #   - 删除桶中的所有文件碎片（找到桶中所有的文件碎片并删除）
    #   - 删除桶中
    delete_bucket_files(request.tracer.project.bucket, request.tracer.project.region)

    # todo 2、删除数据库中的项目
    request.tracer.project.delete()

    return redirect(reverse('web:project_list'))


def setting_change_pwd(request, project_id):
    if request.method == 'GET':
        return render(request, 'web/setting_change_pwd.html')
    if request.method == 'POST':
        form = ChangePasswordForm(request, data=request.POST)
        if form.is_valid():
            request.tracer.user.password = form.cleaned_data['new_password']
            request.tracer.user.save()
            return JsonResponse({'status': True})

        return JsonResponse({'status': False})






