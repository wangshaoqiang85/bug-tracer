import collections
from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from web.models import *


def statistics(request, project_id):
    """项目统计"""
    return render(request, 'web/statistics.html')


def statistics_priority(request, project_id):
    """优先级饼图"""
    """找到时间区间内所有的问题，根据优先级分组， 每个优先级的问题数量"""

    start = request.GET.get('start')
    end = request.GET.get('end')
    # print(start,'----', end)

    # 1、构造字典
    data_dict = collections.OrderedDict()
    for key, text in Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}

    # 2、去数据库中查询数据
    result = Issues.objects.filter(project_id=project_id,
                                   create_datetime__gte=start,
                                   create_datetime__lt=end).values('priority').annotate(ct=Count('id'))
    # print(result)
    # 3、将数据添加到字典中
    for item in result:
        data_dict[item['priority']]['y'] = item['ct']

    return JsonResponse({'status': True, 'data': list(data_dict.values())})


def statistics_project_user(request, project_id):
    """任务成员配比"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    """
        info = {
            1:{
                name:"武沛齐",
                status:{
                    1:0,
                    2:1,
                    3:0,
                    4:0,
                    5:0,
                    6:0,
                    7:0,
                }
            },
            2:{
                name:"王洋",
                status:{
                    1:0,
                    2:0,
                    3:1,
                    4:0,
                    5:0,
                    6:0,
                    7:0,
                }
            }
        }
        """
    # 1、所有项目成员以及未指派
    all_user_dict = collections.OrderedDict()
    all_user_dict[request.tracer.project.creator.id] = {
        'name': request.tracer.project.creator.username,
        'status': {item[0]: 0 for item in Issues.status_choices}
    }
    all_user_dict[None] = {
        'name': '未指派',
        'status': {item[0]: 0 for item in Issues.status_choices}
    }
    user_list = ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            'name': item.user.username,
            'status': {item[0]: 0 for item in Issues.status_choices}
        }

    # 2、数据库中获取数据
    issues = Issues.objects.filter(
        project_id=project_id,
        create_datetime__gte=start,
        create_datetime__lt=end
    )
    for item in issues:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1
    # print(all_user_dict)

    # 3、获取所有项目成员
    categories = [data['name'] for data in all_user_dict.values()]

    # 4、构造series字典
    """
        data_result_dict = {
            1:{name:新建,data:[1，2，3，4]},
            2:{name:处理中,data:[3，4，5]},
            3:{name:已解决,data:[]},
            4:{name:已忽略,data:[]},
            5:{name:待反馈,data:[]},
            6:{name:已关闭,data:[]},
            7:{name:重新打开,data:[]},
        }
    """
    data_result_dict = collections.OrderedDict()
    colors = ['rgb(124, 181, 236)', 'rgb(241, 92, 128)',
              'rgb(144, 237, 125)', 'rgb(247, 163, 92)',
              'rgb(128, 133, 233)', 'rgb(67, 67, 72)',
              'rgb(228, 211, 84)', ]
    for item in Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], 'data': [], 'color': colors[item[0]-1]}

    for key, text in Issues.status_choices:
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    context = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        }
    }
    return JsonResponse(context)
