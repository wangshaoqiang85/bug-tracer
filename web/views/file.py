from django.shortcuts import render, reverse
from django.http import JsonResponse, HttpResponse
from django.forms import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction   # 事务
from web.forms.file import FolderModelForm, FileModelForm
from web.models import FileRepository,Project

from utils.tencent.cos import delete_file, delete_file_list, credential
import json
import requests


# http://127.0.0.1:8000/manage/3/file/
# http://127.0.0.1:8000/manage/3/file/?folder=9
def file(request, project_id):
    parent_object = None
    folder_id = request.GET.get('folder', '')
    if folder_id.isdecimal():
        parent_object = FileRepository.objects.filter(
            id=int(folder_id),
            project=request.tracer.project,
            file_type=2).first()

    # get请求, 查看页面
    if request.method == 'GET':
        # 文件导航条获取，循环获取父级目录的名称
        breadcrumb_list = []
        parent = parent_object
        while parent:
            # breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            breadcrumb_list.insert(0, model_to_dict(parent, fields=['id', 'name']))
            parent = parent.parent

        # 获取当前文件夹下的所有文件名
        queryset = FileRepository.objects.filter(project=project_id)
        if not parent_object:
            folder_list = queryset.filter(parent__isnull=True).order_by('-file_type')
        else:
            folder_list = queryset.filter(parent=parent_object).order_by('-file_type')

        form = FolderModelForm(request, parent_object)
        # 上下文
        context = {
            'form': form,
            'folder_list': folder_list,          # 文件夹列表
            'breadcrumb_list': breadcrumb_list,  # 文件夹导航条
            'folder_object': parent_object       # 父级文件夹
        }
        return render(request, 'web/file.html', context)

    # 如果是post请求，添加文件夹或者修改文件夹
    fid = request.POST.get('fid', '')  # 获取需要编辑的文件夹名称
    edit_object = None  # 需要编辑的文件夹
    # 如果需要编辑的文件夹id 存在就获取需要编辑的文件夹对象
    if fid.isdecimal():
        edit_object = FileRepository.objects.filter(id=int(fid), project_id=project_id, file_type=2).first()

    if edit_object:
        # 将需要编辑的文件夹对象传给表单类验证
        form = FolderModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        # 新建文件夹直接POST数据传给表单类
        form = FolderModelForm(request, parent_object, data=request.POST)

    if form.is_valid():
        form.instance.file_type = 2
        form.instance.update_user = request.tracer.user
        form.instance.project = request.tracer.project
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):
    """删除文件"""
    fid = request.GET.get('fid')

    delete_object = FileRepository.objects.filter(id=int(fid), project_id=project_id).first()
    # cos操作需要传递的参数
    bucket_name = request.tracer.project.bucket  # 桶名称
    region = request.tracer.project.region   # 桶所在的区域
    key = delete_object.key    # 要删除的文件名称

    if delete_object.file_type == 1:
        # todo 删除文件（数据库文件删除， cos文件删除，项目已经使用的空间更新）
        # 1、归还项目已经使用空间
        request.tracer.project.use_space -= delete_object.file_size    # 文件空间使用字节为单位
        request.tracer.project.save()

        # 2、cos 文件删除
        delete_file(bucket_name, region, key)

        # 3、数据库中删除文件
        delete_object.delete()

        return JsonResponse({'status': True})

    else:
        # todo 删除文件夹（找到文件夹中的所有文件数据库文件删除， cos文件删除，项目已经使用的空间更新）
        total_size = 0
        delete_key_list = []
        # 1、使用队列遍历文件夹及其所有子文件夹, 找到所有需要删除的文件
        folder_list = [delete_object]
        for folder in folder_list:
            child_list = FileRepository.objects.filter(project_id=project_id, parent=folder).order_by('-file_type')
            for child in child_list:
                if child.file_type == 2:
                    # 如果是文件夹加入到队列中
                    folder_list.append(child)
                else:
                    # 如果是文件，计算容量，将文件存储在COS中的名称加入到删除列表，不放入队列
                    total_size += child.file_size

                    delete_key_list.append({'Key': child.key})

        # 2、cos中批量删除
        if delete_key_list:
            delete_file_list(bucket_name, region, delete_key_list)

        # 3、归还项目已经使用空间
        if total_size:
            request.tracer.project.use_space -= total_size  # 文件空间使用字节为单位
            request.tracer.project.save()

        # 4、数据库中删除文件
        delete_object.delete()
        return JsonResponse({'status': True})


@csrf_exempt
def cos_credential(request, project_id):
    """获取上传的临时凭证"""

    file_list = json.loads(request.body.decode('utf-8'))
    # print(file_list)
    per_file_limit = request.tracer.price_policy.per_file_size * 1024 * 1024  # 每个项目中单个文件大小限制 (MB 转 B)
    total_file_limit = request.tracer.price_policy.project_space * 1024 * 1024  # 单个项目总空间  (MB 转 B)
    cur_use_space = Project.objects.get(id=project_id).use_space   # 项目已经使用的空间

    # 检查文件大小是否符合要求
    total_size = 0
    for item in file_list:
        # 文件的字节大小 item['size'] = B
        # 单文件限制的大小 M
        if item['size'] > per_file_limit:
            err_msg = "单文件超出限制（最大{}MB），文件：{}，请升级套餐。".format(request.tracer.price_policy.per_file_size, item['name'])
            return JsonResponse({'status': False, 'error': err_msg})
        total_size += item['size']

    # 上传的文件总容量校验
    if total_size + cur_use_space > total_file_limit:
        msg = "项目总容量超出限制（最大{}MB）,请升级套餐".format(request.tracer.price_policy.project_space)
        return JsonResponse({'status': False, 'error': msg})

    # todo 校验当前文件夹中是否已经存在这个文件名

    # 文件大小符合要求，获取临时密钥
    bucket = request.tracer.project.bucket
    region = request.tracer.project.region
    data_dict = credential(bucket, region)

    # print(data_dict)
    return JsonResponse({'status': True, 'data': data_dict})


@csrf_exempt
def file_post(request, project_id):

    # print(request.POST)
    # 'name': fileName,
    # 'key': key,
    # 'file_size': fileSize,
    # 'parent': CURRENT_FOLDER_ID,
    # 'etag': data.ETag,
    # 'file_path': data.Location,

    form = FileModelForm(request, data=request.POST)
    if form.is_valid():
        # 通过ModelForm.save存储到数据库中的数据返回的isntance对象，无法通过get_xx_display获取choice的中文
        # form.instance.file_type = 1
        # form.update_user = request.tracer.user
        # instance = form.save() # 添加成功之后，获取到新添加的那个对象（instance.id,instance.name,instance.file_type,instace.get_file_type_display()

        data_dict = form.cleaned_data
        data_dict.pop('etag')  # 把etag这个字段去掉，因为数据库的表中没有这个字段
        # 写入数据库
        data_dict.update({
            'project': request.tracer.project,
            'file_type': 1,
            'update_user': request.tracer.user,
        })

        # todo 设置事务
        try:
            with transaction.atomic():
                instance = FileRepository.objects.select_for_update().create(**data_dict)
                # 更新这个项目的已经使用空间
                #
                # 这样写不行， 有并发问题，因为前端多个ajax发送过来的request.tracer.project不是更新之后的project对象
                # request.tracer.project.use_space += instance.file_size
                # request.tracer.project.save()
                #
                project_object = Project.objects.select_for_update().get(id=project_id)
                # print('-'*66)
                # print('原来空间：', project_object.use_space)
                project_object.use_space += data_dict['file_size']
                project_object.save()
                # print('之后空间：', project_object.use_space)
                # print('-'*66)

        except Exception as e:
            # todo 如果保存失败，应该把这个文件从cos中删除

            return JsonResponse({'status': False})

        # 日期格式化
        file_time = instance.update_datetime.timetuple()
        file_time = str(file_time.tm_year)+'年'+str(file_time.tm_mon)+'月'+str(file_time.tm_mday)+"日 "+\
                    str(file_time.tm_hour+8)+':'+str(file_time.tm_min)
        data = {
            'id': instance.id,
            'name': instance.name,
            # 'file_type': instance.file_type,
            'file_size': instance.file_size,
            'update_user': instance.update_user.username,
            'update_datetime': file_time,
            # strftime("%Y{}%m{}%d{} %H:%M").format('年', '月', '日'),
            'download_url': reverse('web:file_download', kwargs={'project_id': project_id, 'file_id': instance.id})

        }
        return JsonResponse({'status': True, 'data': data})

    return JsonResponse({'status': False, 'error': form.errors})


def file_download(request, project_id, file_id):
    """下载文件"""

    file_object = FileRepository.objects.filter(id=file_id, project_id=project_id).first()
    print(file_object.file_path)
    res = requests.get(file_object.file_path)

    # 支持大文件下载
    data = res.iter_content()

    # 设置content_type='application/octet-stream'， 用于提示下载框
    response = HttpResponse(data, content_type='application/octet-stream')

    # 设置响应头；如果是中文名需要转义
    from django.utils.encoding import escape_uri_path
    file_name = escape_uri_path(file_object.name)
    response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)

    return response


