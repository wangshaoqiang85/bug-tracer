
'''将已经登录的用户信息保存到request中的中间件'''

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.shortcuts import redirect,reverse
from web.models import UserInfo,Transaction,PricePolicy, Project,ProjectUser
import datetime


class Tracer(object):

    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """如果用户已经登录，就在request中赋值"""
        user_id = request.session.get('user_id', 0)
        user_object = UserInfo.objects.filter(id=user_id).first()

        # request.tracer = user_object
        '''使用自定义的类来存储用户信息和用户额度'''
        request.tracer = Tracer()
        request.tracer.user = user_object

        # 白名单：没有登录就可以访问的页面
        '''
        1、获取当前用户访问的url
        2、检查URL 是否在白名单中，如果在则可以继续向后访问，如果不在，则判断是否已经登录
        '''
        # request.path_info得到当前页面的URL
        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return

        # 如果没有登录，跳转到登录页面
        if not request.tracer.user:
            return redirect(reverse('web:login'))

        '''登录成功之后，访问后台管理时：获取当前用户所拥有的额度'''
        # 方式一  免费额度在交易记录中存储的情况
        # 获取当前用户ID值最大（最近的交易记录）
        _object = Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        # 判断是否已经过期
        current_datetime = datetime.datetime.now()
        # 有收费版的支付记录，但是过期了
        if _object.end_datetime and _object.end_datetime < current_datetime:
            # 设置成免费版的额度
            _object = Transaction.objects.first(user=user_object, status=2, price_policy=1).first()

        request.tracer.price_policy = _object.price_policy

        # 方式二，如果免费版的不添加交易记录，而是使用配置文件时使用
        '''
        # 获取当前用户ID值最大（最近交易记录）
        _object = Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()

        if not _object:
            # 没有购买
            request.price_policy = PricePolicy.objects.filter(category=1, title="个人免费版").first()
        else:
            # 付费版
            current_datetime = datetime.datetime.now()
            if _object.end_datetime and _object.end_datetime < current_datetime:
                request.price_policy = PricePolicy.objects.filter(category=1, title="个人免费版").first()
            else:
                request.price_policy = _object.price_policy
        '''

    def process_view(self,request, view, args, kwargs):
        # 判断url是否是manage开头，如果是则判断项目是否是有当前用户创建或参与的
        if not request.path_info.startswith('/manage/'):
            return

        project_id = kwargs.get('project_id')
        # 是否由我创建
        project_object = Project.objects.filter(creator=request.tracer.user, id=project_id).first()
        if project_object:
            # 如果是我创建的就通过
            request.tracer.project = project_object
            return

        # 是否是我参与的
        project_user_object = ProjectUser.objects.filter(user=request.tracer.user, project_id=project_id).first()
        if project_user_object:
            request.tracer.project = project_user_object.project
            return

        return redirect(reverse('web:project_list'))





