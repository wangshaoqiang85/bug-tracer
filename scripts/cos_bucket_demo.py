# -*- coding=utf-8
# appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # 这行代码可以自动输出response

secret_id = 'AKIDWkiRN4NfZFemeJJwtYJo20hALn48HnNv'      # 替换为用户的 secretId
secret_key = 'NVM3T3NGuHPHt42jRCj0hIf9NON7bqpl'      # 替换为用户的 secretKey
region = 'ap-beijing'     # 替换为用户的 Region


config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
# 2. 获取客户端对象
client = CosS3Client(config)

# 创建桶
response = client.create_bucket(
    Bucket='demo2-1300263909',
    ACL='public-read'  # private / public-read / public-read-write
)

