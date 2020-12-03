import datetime
import time
import collections

from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from web.models import *


def dashboard(request, project_id):
    """项目概览"""
    # 项目对象可以从数据库获取，也可以从request.tracer.project中获取
    # project_object = Project.objects.filter(id=project_id).first()

    # ##### 问题数据按照状态分类处理
    status_dict = {}
    for key, text in Issues.status_choices:
        status_dict[key] = {'text': text, 'count': 0}

    issues_data = Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count('id'))
    # print(issues_data)
    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']
    # print(status_dict)

    # ##### 项目成员展示, 项目的参与者从request.tracer.project.creator中获取
    project_user = ProjectUser.objects.filter(project_id=project_id).values('user_id', 'user__username')
    # print(project_user)

    # ##### 项目动态， 问题被指派给了谁
    assign_object = Issues.objects.filter(project_id=project_id, assign__isnull=False)[:10]

    context = {
        'status_dict': status_dict,
        'project_user': project_user,
        'assign_object': assign_object,
    }
    return render(request, 'web/dashboard.html', context)


def issues_chart(request, project_id):
    """概览界面生成highcharts绘图需要的数据"""
    """获取最近30天，每天创建的问题的数量"""
    today = datetime.datetime.now().date()
    # 生成最近30天的时间戳
    date_dict = collections.OrderedDict()
    for i in range(30):
        date = today - datetime.timedelta(days=i)
        date_dict[date.strftime("%Y-%m-%d")] = [time.mktime(date.timetuple()) * 1000, 0]
        # time.mktime(date.timetuple()) * 1000 生成时间戳
    """
    # for j in date_dict.items():
    #     print(j)   
    date_dict 的 部分数据
    {'2020-08-12': [1597161600000.0, 0]}
    {'2020-08-11': [1597075200000.0, 0]}
    {'2020-08-10': [1596988800000.0, 0]}
    {'2020-08-09': [1596902400000.0, 0]}
    ...
    """

    # #### 到数据库中查询最近30天的所有数据
    # select xxxx,1 as ctime from xxxx
    # select id,name,email from table;
    # select id,name, strftime("%Y-%m-%d",create_datetime) as ctime from table;
    # "DATE_FORMAT(web_transaction.create_datetime,'%%Y-%%m-%%d')"
    result = Issues.objects.filter(
        project_id=project_id,
        create_datetime__gte=today-datetime.timedelta(days=30)).extra(
        select={'ctime': "DATE_FORMAT(web_issues.create_datetime,'%%Y-%%m-%%d')"}
    ).values('ctime').annotate(ct=Count('id'))

    # print(result)
    # < QuerySet[{'ctime': '2020-08-07', 'ct': 2}, {'ctime': '2020-08-08', 'ct': 5}, {'ctime': '2020-08-12', 'ct': 1}] >

    # 将获取的数据添加到date_dict中
    for item in result:
        date_dict[item['ctime']][1] = item['ct']

    return JsonResponse({'status': True, 'data': list(date_dict.values())})

