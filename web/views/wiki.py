from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # 装饰视图函数不检查csrf
from web.forms.wiki import WikiAddModelForm
from web.models import Wiki, Project
from utils.encrypt import uid
from utils.tencent.cos import upload_file


def wiki(request, project_id):
    '''Wiki首页'''

    # wiki_id是在url中传递的参数，如果不是空就显示文章详情，否则显示Wiki首页
    wiki_id = request.GET.get('wiki_id')
    if wiki_id and wiki_id.isdecimal():
        wiki_object = Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
        return render(request, 'web/wiki.html', {'wiki_object': wiki_object})
    else:
        return render(request, 'web/wiki.html')


def wiki_add(request, project_id):
    """Wiki添加"""

    if request.method == 'GET':
        form = WikiAddModelForm(request)
        return render(request, 'web/wiki_form.html', {'form': form})
    if request.method == 'POST':
        form = WikiAddModelForm(request, data=request.POST)
        if form.is_valid():
            # todo 使同级目录中的文章不能重名#，判断当前父文章中是否已经存在这个文章名

            # 如果文章有父文章，那么深度就是父文章的深度加一
            # print(form.instance.parent)
            if form.instance.parent:
                form.instance.depth = form.instance.parent.depth + 1

            form.instance.project = request.tracer.project
            form.save()
            return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
        else:
            return render(request, 'web/wiki_form.html', {'form': form})


def wiki_catalog(request, project_id):
    '''显示Wiki目录'''

    # 获取当前项目中的所有wiki文章
    # data = Wiki.objects.filter(project_id=project_id).all().values_list('id', 'title', 'parent')
    # data = Wiki.objects.filter(project_id=project_id).all().values('id', 'title', 'parent_id')
    # 按照深度排序，优先遍历没有父文章的Wiki文章
    data = Wiki.objects.filter(project_id=project_id).all().order_by('depth').values('id', 'title', 'parent_id')

    return JsonResponse({'status': True, 'data': list(data)})


def wiki_delete(request, project_id, wiki_id):
    '''删除Wiki文章'''

    Wiki.objects.filter(project_id=project_id, id=wiki_id).delete()
    return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))


def wiki_edit(request, project_id, wiki_id):
    '''文章编辑'''
    wiki_object = Wiki.objects.filter(project_id=project_id, id=wiki_id).first()
    if not wiki_object:
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))

    if request.method == 'GET':
        form = WikiAddModelForm(request, instance=wiki_object)
        return render(request, 'web/wiki_form.html', {'form': form})

    # 如果是post请求
    form = WikiAddModelForm(request, data=request.POST, instance=wiki_object)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        form.save()
        url = reverse('web:wiki', kwargs={'project_id': project_id})
        preview_url = '{0}?wiki_id={1}'.format(url, wiki_id)
        return redirect(preview_url)

    return render(request, 'web/wiki_form.html', {'form': form})


@csrf_exempt   # 这个装饰器使得视图函数不检查csrf
def wiki_upload(request, project_id):
    '''Wiki的文章中的图片'''

    # markdown上传文件需要的返回值类型
    result = {
        'success': 0,  # 0代表失败; 1代表成功
        'message': None,
        'url': None,
    }

    # 获取markdown上传的文件对象
    image_object = request.FILES.get('editormd-image-file')
    if not image_object:
        result['message'] = '文件不存在'
        return JsonResponse(result)

    # 创建上传之后的文件名,由于腾讯云上传相同的文件名会覆盖原来文件，所以尽量保持文件名唯一
    ext = image_object.name.rsplit('.')[-1]  # 上传的文件后缀名
    # uid是自定义的生成随机字符串的函数,  key是新的文件名
    key = '{}.{}'.format(uid(request.tracer.user.mobile_phone), ext)

    # 获取项目的桶名称
    bucket_name = request.tracer.project.bucket
    region = request.tracer.project.region

    # 上传到腾讯云cos桶中
    image_url = upload_file(bucket_name, region, image_object, key)

    result['success'] = 1
    result['url'] = image_url
    result['message'] = '上传成功'

    return JsonResponse(result)

