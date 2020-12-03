from django.conf.urls import url, include
from web.views import account, home, project, wiki, file, issues, setting, dashboard, statistics
app_name = 'web'
urlpatterns = [
    url(r'^register/$', account.register, name='register'),  # 注册
    url(r'^send/sms/$', account.send_sms, name='send_sms'),  # 发送短信验证码
    url(r'^login/sms/$', account.login_sms, name='login_sms'),  # 手机短信验证码登录
    url(r'^login/$', account.login, name='login'),    # 用户名和密码
    url(r'^logout/$', account.logout, name='logout'),    # 退出登录
    url(r'^image/code/$', account.image_code, name='image_code'),  # 生成图片验证码

    url(r'^$', home.index, name='index'),  # 首页
    url(r'^price/$', home.price, name='price'),  # 价格策略
    url(r'^payment/(?P<policy_id>\d+)$', home.payment, name='payment'),  # 订单
    url(r'^pay/$', home.pay, name='pay'),  # 订单支付
    url(r'^pay/notify/$', home.pay_notify, name='pay_notify'),  # 支付成功之后的页面

    # 项目列表
    url(r'^project/list/$', project.project_list, name='project_list'),  # 项目列表

    url(r'^project/star/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_star, name='project_star'),
    url(r'^project/unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_unstar, name='project_unstar'),

    # 项目管理的界面
    url(r'^manage/(?P<project_id>\d+)/', include([
        # wiki文章相关的路由
        url(r'^wiki/$', wiki.wiki, name='wiki'),
        url(r'^wiki/add/$', wiki.wiki_add, name='wiki_add'),
        url(r'^wiki/catalog/$', wiki.wiki_catalog, name='wiki_catalog'),  # wiki文章目录
        url(r'^wiki/delete/(?P<wiki_id>\d+)/$', wiki.wiki_delete, name='wiki_delete'),  # 删除文章
        url(r'^wiki/edit/(?P<wiki_id>\d+)/$', wiki.wiki_edit, name='wiki_edit'),  # 文章编辑
        url(r'^wiki/upload/$', wiki.wiki_upload, name='wiki_upload'),  # 上传图片

        # file文件相关的路由
        url(r'^file/$', file.file, name='file'),
        url(r'^file/delete/$', file.file_delete, name='file_delete'),
        url(r'^cos/credential/$', file.cos_credential, name='cos_credential'),
        url(r'^file/file_post/$', file.file_post, name='file_post'),  # 文件上传成功之后写入数据库
        url(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),  # 文件下载

        # 项目设置相关的路由
        url(r'^setting/$', setting.setting, name='setting'),
        url(r'^setting/delete/$', setting.setting_delete, name='setting_delete'),
        url(r'^setting/change_pwd$', setting.setting_change_pwd, name='setting_change_pwd'),

        # 项目问题相关的路由
        url(r'^issues/$', issues.issues, name='issues'),
        url(r'^issues/detail/(?P<issues_id>\d+)/$', issues.issues_detail, name='issues_detail'),
        url(r'^issues/record/(?P<issues_id>\d+)/$', issues.issues_record, name='issues_record'),
        url(r'^issues/change/(?P<issues_id>\d+)/$', issues.issues_change, name='issues_change'),
        url(r'^issues/invite/$', issues.issues_invite, name='issues_invite'),

        # 概览部分
        url(r'^dashboard/$', dashboard.dashboard, name='dashboard'),
        url(r'^dashboard/issues/chart/$', dashboard.issues_chart, name='issues_chart'),

        # 统计
        url(r'^statistics/$', statistics.statistics, name='statistics'),
        url(r'^statistics/priority/$', statistics.statistics_priority, name='statistics_priority'),
        url(r'^statistics/project_user/$', statistics.statistics_project_user, name='statistics_project_user'),

    ], None)),

    # 接收邀请
    url(r'^invite/join/(?P<code>\w+)/$', issues.invite_join, name='invite_join'),

]