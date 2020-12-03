# -*- coding=utf-8
# appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

secret_id = 'AKIDWkiRN4NfZFemeJJwtYJo20hALn48HnNv'      # 替换为用户的 secretId
secret_key = 'NVM3T3NGuHPHt42jRCj0hIf9NON7bqpl'      # 替换为用户的 secretKey
region = 'ap-beijing'     # 替换为用户的 Region


config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
# 2. 获取客户端对象
client = CosS3Client(config)

# 上传文件
# 高级上传接口（推荐）
# 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
response = client.upload_file(
    Bucket='demo01-1300263909',
    LocalFilePath='code.png',  # 本地文件的路径
    Key='picture.jpg',  # 上传到腾讯云的名称
)
print(response['ETag'])


