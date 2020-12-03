import math

from django.template import Library
from web.models import Project,ProjectUser
from django.urls import reverse


register = Library()


# 使用inclusion_tag在多个网页的导航栏中展示项目名称
@register.inclusion_tag('inclusion/all_project_list.html')
def all_project_list(request):
    # 获取我创建的项目
    my_project = Project.objects.filter(creator=request.tracer.user).all()

    # 获取我参与的项目
    join_project = ProjectUser.objects.filter(user=request.tracer.user).all()

    return {'my': my_project, 'join': join_project, 'request': request}


# 使用inclusion_tag使导航栏中选中的部分呈现选中状态
@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data_list = [
        {'title': '概览', 'url': reverse("web:dashboard", kwargs={'project_id': request.tracer.project.id})},
        {'title': '问题', 'url': reverse("web:issues", kwargs={'project_id': request.tracer.project.id})},
        {'title': '统计', 'url': reverse("web:statistics", kwargs={'project_id': request.tracer.project.id})},
        {'title': 'wiki', 'url': reverse("web:wiki", kwargs={'project_id': request.tracer.project.id})},
        {'title': '文件', 'url': reverse("web:file", kwargs={'project_id': request.tracer.project.id})},
        {'title': '设置', 'url': reverse("web:setting", kwargs={'project_id': request.tracer.project.id})},
    ]

    for item in data_list:
        if request.path_info.startswith(item['url']):
            item['class'] = 'active'

    return {'data_list': data_list}


# 自定义的文件大小转化过滤器，字节单位转 KB
@register.filter
def div(num):
    """除法过滤器"""
    return math.ceil(num / 1024)


# 使用simple_tag将问题id变成 008 的形式展示
@register.simple_tag
def string_just(issues_id):
    res = str(issues_id).rjust(3, '0')
    return res


# 项目已经使用空间的单位转换
@register.simple_tag
def use_space(size):
    if size > 1024 * 1024 * 1024:
        return '%.2f GB' % (size/1024/1024/1024)
    elif size > 1024 * 1024:
        return '%.2f MB' % (size/1024/1024)
    elif size > 1024:
        return '%.2f KB' % (size/1024)
    else:
        return '%.2f B' % size





