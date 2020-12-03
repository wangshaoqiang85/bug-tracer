from django.shortcuts import render,redirect,reverse
from django.http import JsonResponse,HttpResponse
from utils.tencent.cos import creat_bucket  # 自定义的创建cos桶
from web.forms.project import ProjectModelForm
from web.models import *
import time


def project_list(request):
    """项目列表"""
    if request.method == 'GET':
        """
        1. 从数据库中获取两部分数据
            我创建的所有项目：已星标、未星标
            我参与的所有项目：已星标、未星标
        2. 提取已星标
            列表 = 循环 [我创建的所有项目] + [我参与的所有项目] 把已星标的数据提取

        得到三个列表：星标、创建、参与
        """
        project_dict = {'star': [], 'join': [], 'my': []}

        my_project_list = Project.objects.filter(creator=request.tracer.user).order_by('id')
        for row in my_project_list:
            if row.star:
                project_dict['star'].append({'value': row, 'type': 'my'})
            else:
                project_dict['my'].append(row)

        join_project_list = ProjectUser.objects.filter(user=request.tracer.user).order_by('id')
        for item in join_project_list:
            if item.star:
                project_dict['star'].append({'value':item.project, 'type':'join'})
            else:
                project_dict['join'].append(item.project)

        form = ProjectModelForm(request)
        return render(request, 'web/project_list.html', {'form': form, 'project_dict': project_dict})

    if request.method == 'POST':
        '''前端发送Ajax的post请求创建项目'''

        form = ProjectModelForm(request, data=request.POST)

        if form.is_valid():
            # 1、保存项目之前创建cos桶
            time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))   # 时间戳格式化
            bucket_name = '{0}-{1}-1300263909'.format(request.tracer.user.mobile_phone, time_str)
            region = 'ap-beijing'
            creat_bucket(bucket_name, region=region)
            # 保存项目的腾讯云cos桶名称和区域
            form.instance.bucket = bucket_name
            form.instance.region = region

            # 2、验证通过,获取当前登录用户之后， 将项目保存到数据库
            form.instance.creator = request.tracer.user
            instance = form.save()

            # 3、给项目默认添加问题类型
            issues_type_list = []
            for issues_type in IssuesType.PROJECT_INIT_LIST:  # ["任务", '功能', 'Bug']
                issues_type_list.append(IssuesType(title=issues_type, project=instance))
            # 批量加入到数据库中  bulk_create
            IssuesType.objects.bulk_create(issues_type_list)

            return JsonResponse({'status': True})
        # 验证失败
        return JsonResponse({'status': False, 'error': form.errors})

# 设置星标
# /project/star/my/1
# /project/star/join/1
def project_star(request, project_type, project_id):
    if project_type == 'my':
        Project.objects.filter(creator=request.tracer.user,id=project_id).update(star=True)
        return redirect(reverse('web:project_list'))
    if project_type == 'join':
        ProjectUser.objects.filter(user=request.tracer.user,project_id=project_id).update(star=True)
        return redirect(reverse('web:project_list'))


# 取消星标
def project_unstar(request, project_type, project_id):
    if project_type == 'my':
        Project.objects.filter(creator=request.tracer.user,id=project_id).update(star=False)
        return redirect(reverse('web:project_list'))

    if project_type == 'join':
        ProjectUser.objects.filter(user=request.tracer.user,project_id=project_id).update(star=False)
        return redirect(reverse('web:project_list'))

    return HttpResponse('请求错误')
