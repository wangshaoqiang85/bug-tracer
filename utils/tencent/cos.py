from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos.cos_exception import CosServiceError
from django.conf import settings


# secret_id = ''      # 替换为用户的 secretId
# secret_key = ''      # 替换为用户的 secretKey
# region = 'ap-beijing'     # 替换为用户的 Region

def creat_bucket(bucket_name, region='ap-beijing'):

    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    # 2. 获取客户端对象
    client = CosS3Client(config)

    # 创建桶
    response = client.create_bucket(
        Bucket=bucket_name,  # 桶的名称
        ACL='public-read',   # private / public-read / public-read-write
    )

    # 设置桶的跨域规则
    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                'AllowedHeader': "*",
                'ExposeHeader': "*",
                'MaxAgeSeconds': 500
            }
        ]
    }
    client.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration=cors_config
    )


def upload_file(bucket_name, region, file_oject, key):
    """上传图片是经过后台处理的post请求"""

    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    client = CosS3Client(config)

    # 使用文件对象上传（文件流read方法）
    response = client.upload_file_from_buffer(
        Bucket=bucket_name,
        Body=file_oject,  # 本地文件的路径
        Key=key  # 上传到腾讯云的名称
    )
    # print(response['ETag'])

    # 返回上传成功的图片路径
    # https://demo01-1300263909.cos.ap-beijing.myqcloud.com/picture.jpg
    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket_name, region, key)


def delete_file(bucket_name, region, key):
    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    client = CosS3Client(config)

    response = client.delete_object(
        Bucket=bucket_name,
        Key=key  # 腾讯云中文件的名称
    )
    # print(response['ETag'])


def check_file(bucket_name, region, key):
    '''获取cos中的文件信息'''
    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    client = CosS3Client(config)

    response = client.head_object(
        Bucket=bucket_name,
        Key=key  # 腾讯云中文件的名称
    )
    # print(response['ETag'])
    return response


def delete_file_list(bucket_name, region, key_list):
    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    client = CosS3Client(config)
    # 批量删除文件, 传递参数的格式
    # objects = {
    #     "Quiet": "true",
    #     "Object": [
    #         {
    #             "Key": "file_name1"
    #         },
    #         {
    #             "Key": "file_name2"
    #         }
    #     ]
    # }
    objects = {
        "Quiet": "true",
        "Object": key_list,
    }
    # 批量删除文件
    response = client.delete_objects(
        Bucket=bucket_name,
        Delete=objects  # 腾讯云中文件的名称的集合
    )


def credential(bucket_name, region):
    """ 获取cos上传临时凭证 """

    from sts.sts import Sts

    config = {
        # 临时密钥有效时长，单位是秒（30分钟=1800秒）
        'duration_seconds': 1800,
        # 固定密钥 id
        'secret_id': settings.TX_COS_SECRET_ID,
        # 固定密钥 key
        'secret_key': settings.TX_COS_SECRET_KEY,
        # 换成你的 bucket
        'bucket': bucket_name,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            # "name/cos:PutObject",
            # 'name/cos:PostObject',
            # 分片上传
            # 'name/cos:DeleteObject',
            # "name/cos:UploadPart",
            # "name/cos:UploadPartCopy",
            # "name/cos:CompleteMultipartUpload",
            # "name/cos:AbortMultipartUpload",
            "*",  # '*'代表所有请求类型
        ],

    }

    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict


def delete_bucket_files(bucket_name, region):
    '''删除桶中所有的文件和文件碎片'''

    config = CosConfig(Region=region, SecretId=settings.TX_COS_SECRET_ID, SecretKey=settings.TX_COS_SECRET_KEY)
    client = CosS3Client(config)

    try:
        # 找到所有的文件并删除
        while True:
            all_file_objects = client.list_objects(bucket_name)  # 获取1000个文件对象

            if not all_file_objects.get('Contents'):
                break
            objects = {"Quiet": "true",
                       "Object": [{"Key": item["Key"]} for item in all_file_objects.get('Contents')]
                       # "Object": [{"Key": "file_name1"}, {"Key": "file_name2"}]
                       }

            client.delete_objects(Bucket=bucket_name, Delete=objects)

            if all_file_objects.get('IsTruncated') == 'false':
                break

        # 找到所有的文件碎片并删除
        while True:
            part_uploads = client.list_multipart_uploads(bucket_name)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket_name, item['Key'], item['UploadId'])
            if part_uploads['IsTruncated'] == "false":
                break

        response = client.delete_bucket(Bucket=bucket_name)

    except CosServiceError as e:
        pass



