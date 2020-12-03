import pytz
import json
import datetime
from django.shortcuts import render,reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from web.forms.issues import IssuesModelForm, InviteModelForm
from web.models import *
from utils.pagination import Pagination
from utils.encrypt import uid


# 筛选框利用可迭代对象实现
class CheckFilter(object):
    def __init__(self, name, datalist, request):
        self.name = name   # 筛选的字段名
        self.datalist = datalist   # 模型中name字段对应的choices
        self.request = request  # 便于获取url中的name字段的所有查询条件 例如 status=1&status=2

    def __iter__(self):

        for item in self.datalist:
            key = str(item[0])
            text = item[1]

            # todo 根据url显示选中的框
            value_list = self.request.GET.getlist(self.name)  # 当前url中字符串形式的列表 ['1','2',,,]
            # print('点击之前的value：', value_list)
            # 初始生成每一个多选框对应的链接是
            # /manage/4/issues/?issues_type=4
            # /manage/4/issues/?issues_type=5
            # 如果选中issues_type=4 的多选框之后，
            # 它本身的url会变成/manage/4/issues/，点击链接跳转到没有issues_type=4的条件中
            # 其他多选框的url会在之前的基础上加上issues_type=4，变成/manage/4/issues/?issues_type=4&issues_type=5
            ck = ''
            if key in value_list:
                ck = 'checked'
                value_list.remove(key)
            else:
                value_list.append(key)
            # print('点击之后的value：', value_list)
            # todo 为自己生成URL
            # 在当前的url的基础上增加一项
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            # 当筛选条件变化时，去掉之前的页面，从第一页展示
            if 'page' in query_dict:
                query_dict.pop('page')

            # 筛选条件都去掉时会产生问号，去掉这个问号
            param_url = query_dict.urlencode()   # 将字典中的内容编码成url格式  /status=2/page=2/  这种格式
            if param_url:
                url = '{}?{}'.format(self.request.path_info, query_dict.urlencode())
            else:
                url = self.request.path_info
            # print('当前这个input的url：', url)
            tpl = '<a class="cell" href="{url}"><input type="checkbox" {ck} /><label>{text}</label></a>'
            html = tpl.format(url=url, ck=ck, text=text)
            # print(html)
            # print('-------------------------------------------------')
            yield mark_safe(html)


class SelectFilter(object):
    def __init__(self, name, datalist, request):
        self.name = name
        self.datalist = datalist
        self.request = request

    def __iter__(self):
        yield mark_safe("<select class='select2' multiple='multiple' style='width:100%;'>")
        for item in self.datalist:
            key = str(item[0])
            text = item[1]

            selected = ''
            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                selected = 'selected'
                value_list.remove(key)
            else:
                value_list.append(key)

            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            # 当筛选条件变化时，去掉之前的页面，从第一页展示
            if 'page' in query_dict:
                query_dict.pop('page')

            # 筛选条件都去掉时会产生问号，去掉这个问号
            param_url = query_dict.urlencode()
            if param_url:
                url = '{}?{}'.format(self.request.path_info, query_dict.urlencode())
            else:
                url = self.request.path_info

            html = "<option value='{url}' {selected}>{text}</option>".format(url=url,selected=selected, text=text)
            yield mark_safe(html)

        yield mark_safe("</select>")


def issues(request, project_id):
    """问题首页"""
    if request.method == 'GET':
        form = IssuesModelForm(request)
        invite_form = InviteModelForm()
        # ####### 根据条件查询
        # 根据URL做筛选，筛选条件（根据用户通过GET传过来的参数实现）
        # ?status=1&status=2&issues_type=1
        allow_filter_name = ['issues_type', 'priority', 'status', 'assign', 'attention']
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition['{}__in'.format(name)] = value_list
        """
        condition = {
            "status__in":[1,2],
            'issues_type__in':[1,]
        }
        """

        # ####### 分页展示
        queryset = Issues.objects.filter(project_id=project_id).filter(**condition)
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=3
        )
        issues_object_list = queryset[page_object.start:page_object.end]  # 分页之后的对象

        issues_type_choices = IssuesType.objects.filter(project_id=project_id).values_list('id', 'title')
        project_user_choices = [(request.tracer.project.creator.id, request.tracer.project.creator.username)]
        project_user = ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username')
        project_user_choices.extend(project_user)
        context = {
            'form': form,
            'invite_form': invite_form,
            'issues_object_list': issues_object_list,
            'page_html': page_object.page_html(),
            'filter_list': [
                {'title': '问题类型', 'filter': CheckFilter('issues_type', issues_type_choices, request)},
                {'title': '状态', 'filter': CheckFilter('status', Issues.status_choices, request)},
                {'title': '优先级', 'filter': CheckFilter('priority', Issues.priority_choices, request)},
                {'title': '指派人', 'filter': SelectFilter('assign', project_user_choices, request)},
                {'title': '关注者', 'filter': SelectFilter('attention', project_user_choices, request)},

            ],
            #
            # 'status_list': CheckFilter('status', Issues.status_choices, request),
            # 'priority_list': CheckFilter('priority', Issues.priority_choices, request),
            # 'issues_type_list': CheckFilter('issues_type', issues_type_choices, request)
            #
        }

        return render(request, 'web/issues.html', context)

    # POST方法
    if request.method == 'POST':
        form = IssuesModelForm(request, data=request.POST)
        if form.is_valid():

            form.instance.project_id = project_id
            form.instance.creator = request.tracer.user

            form.save()
            return JsonResponse({'status': True})

        return JsonResponse({'status': False, 'error': form.errors})


def issues_detail(request, project_id, issues_id):
    """问题编辑"""
    issues_object = Issues.objects.filter(id=issues_id, project_id=project_id).first()
    form = IssuesModelForm(request, instance=issues_object)
    return render(request, 'web/issues_detail.html', {'form': form, 'issues_object': issues_object})


@csrf_exempt
def issues_record(request, project_id, issues_id):
    if request.method == 'GET':
        replay_list = IssuesReply.objects.filter(issues_id=issues_id, issues__project_id=project_id)
        data_list = []
        for row in replay_list:
            data = {
                'id': row.id,
                'reply_type_text': row.get_reply_type_display(),
                'content': row.content,
                'creator': row.creator.username,
                'datetime': row.create_datetime.strftime("%Y-%m-%d %H:%M"),  # 如果时间格式含有中文需要特殊处理
                'parent_id': row.reply_id,

            }
            if row.reply:
                data['parent_name'] = row.reply.creator.username
            data_list.append(data)

        return JsonResponse({'status': True, 'data': data_list})

    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        # 校验合法性
        if not content:
            return JsonResponse({'status': False, 'error': "请输入要回复的内容"})
        if parent_id and not IssuesReply.objects.filter(id=parent_id, issues_id=issues_id).exists():
            return JsonResponse({'status': False, 'error': "您要回复的评论或变更记录不存在"})

        reply_object = IssuesReply.objects.create(
            reply_type=2,
            issues_id=issues_id,
            content=content,
            creator=request.tracer.user,
            reply_id=parent_id,
        )
        info = {
            'id': reply_object.id,
            'reply_type_text': reply_object.get_reply_type_display(),
            'content': reply_object.content,
            'creator': reply_object.creator.username,
            'datetime': reply_object.create_datetime.strftime("%Y-%m-%d %H:%M"),  # 如果时间格式含有中文需要特殊处理
            'parent_id': reply_object.reply_id,
        }
        return JsonResponse({'status': True, 'data': info})


@csrf_exempt
def issues_change(request, project_id, issues_id):
    issues_object = Issues.objects.filter(id=issues_id, project_id=project_id).first()
    # 接收数据并处理成json格式
    post_dict = json.loads(request.body.decode('utf-8'))
    # {'name': 'issues_type', 'value': '5'}
    # {'name': 'issues_type', 'value': '5'}
    # {'name': 'start_date', 'value': '2020-08-29'}
    print(post_dict)

    name = post_dict.get('name')
    value = post_dict.get('value')
    field_object = Issues._meta.get_field(name)  # 获取该类内指定字段信息（对象）

    def create_reply_record(change_record):
        # 保存问题变更记录
        reply_object = IssuesReply.objects.create(
            reply_type=1,
            issues_id=issues_id,
            content=change_record,
            creator=request.tracer.user,
        )
        data = {
            'id': reply_object.id,
            'reply_type_text': reply_object.get_reply_type_display(),
            'content': reply_object.content,
            'creator': reply_object.creator.username,
            'datetime': reply_object.create_datetime.strftime("%Y-%m-%d %H:%M"),  # 如果时间格式含有中文需要特殊处理
        }
        return data

    # 1、文本字段的修改
    if name in ['subject', 'desc', 'start_date', 'end_date']:
        if not value:
            # 如果值为空需要判断数据库中的这个字段是否允许为空
            if field_object.null:
                # 如果允许为空
                setattr(issues_object, name, None)  # 用于设置属性值，该属性不一定是存在的
                issues_object.save()
                change_record = '{}更新为空'.format(field_object.verbose_name)
            else:
                return JsonResponse({'status': False, 'error': '这个字段值不能为空！'})
        else:
            setattr(issues_object, name, value)
            issues_object.save()
            change_record = '{}更新为{}'.format(field_object.verbose_name, value)

        data = create_reply_record(change_record)
        return JsonResponse({"status": True, 'data': data})

    # 2、foreign字段的修改(更新指派人时，需要判断是否是这个项目的创建者或者参与者)
    if name in ['project', 'issues_type', 'module', 'assign', 'parent']:
        if not value:
            # 如果值为空需要判断数据库中的这个字段是否允许为空
            if field_object.null:
                # 如果允许为空
                setattr(issues_object, name, None)
                issues_object.save()
                change_record = '{}更新为空'.format(field_object.verbose_name)
            else:
                return JsonResponse({'status': False, 'error': '这个字段值不能为空！'})
        else:
            # 更新指派人时，需要判断是否是这个项目的创建者或者参与者
            if name == 'assign':
                if int(value) == request.tracer.project.creator_id:
                    instance = request.tracer.project.creator
                else:
                    project_user_object = ProjectUser.objects.filter(user_id=int(value), project_id=project_id).first()
                    if project_user_object:
                        instance = project_user_object.user
                    else:
                        instance = None
                if not instance:
                    return JsonResponse({'status': False, 'error': '您选择的用户不存在！'})
            else:
                # 先判断传入的外键是否是这个项目中的外键
                # field_object.rel.model 找到外键的模型类
                instance = field_object.rel.model.objects.filter(id=value, project_id=project_id).first()
                if not instance:
                    return JsonResponse({'status': False, 'error': '您选择的值不存在！'})

            setattr(issues_object, name, instance)
            issues_object.save()
            change_record = '{}更新为{}'.format(field_object.verbose_name, str(instance))

        # 保存问题变更记录
        data = create_reply_record(change_record)
        return JsonResponse({"status": True, 'data': data})

    # 3、choices字段的更新
    if name in ['status', 'mode', 'priority']:
        selected_text = None
        for key, text in field_object.choices:
            if str(key) == value:
                selected_text = text

        if not selected_text:
            return JsonResponse({'status': False, 'error': '这个字段值不能为空！'})

        setattr(issues_object, name, value)
        issues_object.save()
        change_record = '{}更新为{}'.format(field_object.verbose_name, selected_text)

        data = create_reply_record(change_record)
        return JsonResponse({"status": True, 'data': data})

    # 4、多对多键的处理
    # {'name': 'attention', 'value': ['2']}
    if name == 'attention':
        if not value:
            issues_object.attention.set(value)
            issues_object.save()
            change_record = '{}更新为空'.format(field_object.verbose_name)
        else:
            # 获取当前项目的所有成员
            user_list = {str(request.tracer.project.creator.id): request.tracer.project.creator.username}
            project_user_list = ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_list:
                user_list[str(item.user.id)] = item.user.username

            # 判断传入的id是否在当前项目中
            username_list = []
            for user_id in value:
                # if user_id not in user_list.keys():
                #     return JsonResponse({'status': False, 'error': '项目成员不存在！'})
                # username_list.append(user_list.get(user_id))
                username = user_list.get(str(user_id))
                if not username:
                    return JsonResponse({'status': False, 'error': '项目成员不存在！'})

                username_list.append(username)

            issues_object.attention.set(value)
            issues_object.save()
            change_record = '{}更新为{}'.format(field_object.verbose_name, ','.join(username_list))

        data = create_reply_record(change_record)
        return JsonResponse({"status": True, 'data': data})

    # 传入的字段数据库中不存在
    return JsonResponse({'status': False, 'error': '数据库中不存在这个字段！'})


@csrf_exempt
def issues_invite(request, project_id):
    """创建邀请码并返回给前端"""
    form = InviteModelForm(request.POST)
    if form.is_valid():
        # todo 校验用户选中的邀请人数是否在额度范围内

        # 1、只有项目的创建者才能发送邀请链接
        if not request.tracer.project.creator == request.tracer.user:
            form.add_error('period', '无权创建邀请码')
            return JsonResponse({'status': False, 'error': form.errors})

        # 2、设置验证码
        random_invite_code = uid(request.tracer.user.mobile_phone)  # 使用用户手机号创建随机码
        form.instance.creator = request.tracer.user
        form.instance.project = request.tracer.project
        form.instance.code = random_invite_code
        form.save()

        # 3、返回邀请码链接给前端，便于前端页面展示
        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,
            host=request.get_host(),
            path=reverse('web:invite_join', kwargs={'code': random_invite_code})
        )
        return JsonResponse({'status': True, 'url': url})

    return JsonResponse({'status': False, 'error': form.errors})


def invite_join(request, code):
    """加入邀请链接, 注意：这个链接不需要project_id，也没有request.tracer.project"""

    invite_object = ProjectInvite.objects.filter(code=code).first()
    if not invite_object:
        return render(request, 'web/invite_join.html', {'error': '邀请码不存在！'})
    if invite_object.project.creator == request.tracer.user:
        return render(request, 'web/invite_join.html', {'error': '创建者无需再加入项目！'})
    exists = ProjectUser.objects.filter(user=request.tracer.user, project=invite_object.project).exists()
    if exists:
        return render(request, 'web/invite_join.html', {'error': '已加入项目无需再加入！'})

    # ####### 问题1： 最多允许的成员(要进入的项目的创建者的限制）#######
    # max_member = request.tracer.price_policy.project_member # 当前登录用户他限制
    current_time = datetime.datetime.now()    # 是一个offset-naive型，就是一个不含时区的datetime
    print(current_time.tzinfo)
    # 如果没有设置USE_TZ = False，需要手动设置， 即下面这行代码
    # current_time = current_time.replace(tzinfo=pytz.timezone('Asia/shanghai'))
    # 1、邀请码是否过期
    limit_datetime = invite_object.create_datetime + datetime.timedelta(minutes=invite_object.period)
    # 这是offset-aware，是有时区类型（默认UTC类型）
    # 需要在配置文件文件中设置USE_TZ = False，django会根据TIME_ZONE设置的时区进行创建时间并写入数据库，转换成offset-naive型
    print(limit_datetime.tzinfo)
    if current_time > limit_datetime:
        return render(request, 'web/invite_join.html', {'error': '邀请码已过期！'})

    # 2、判断用户购买的额度是否过期, 获取单个项目最多成员数
    max_transaction = Transaction.objects.filter(user=invite_object.project.creator,).order_by('-id').first()
    if max_transaction.price_policy.category == 1:  # 如果是免费版
        max_member = max_transaction.price_policy.project_member
    else:
        if max_transaction.end_datetime < current_time:
            free_object = PricePolicy.objects.filter(category=1).first()
            max_member = free_object.project_member
        else:
            max_member = max_transaction.price_policy.project_member

    # 3、判断目前项目中的成员数量是否在要求范围内（包括创建者和参与者）
    current_member = ProjectUser.objects.filter(project=invite_object.project).count()
    current_member += 1  # 在加上创建者

    if current_member >= max_member:
        return render(request, 'web/invite_join.html', {'error': '项目成员超限，请升级套餐！'})

    # 4、已经邀请的数量是否在用户设置的限制数量内
    # todo 数据库事务上锁，防止异步修改use_count数据
    if invite_object.count:
        if invite_object.use_count >= invite_object.count:
            return render(request, 'web/invite_join.html', {'error': '邀请码数量已使用完！'})

        invite_object.use_count += 1
        invite_object.save()

    # 5、项目参与表中添加记录和更新项目表中的参与人数
    ProjectUser.objects.create(user=request.tracer.user, project=invite_object.project)
    invite_object.project.join_count += 1    # join_count记录当前项目中以及由多少个成员，便于在项目列表页面显示
    invite_object.project.save()

    return render(request, 'web/invite_join.html', {'project': invite_object.project})


