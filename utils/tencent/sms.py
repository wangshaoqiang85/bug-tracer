# -*- coding: utf-8 -*-
from __future__ import print_function

import ssl, hmac, base64, hashlib
from datetime import datetime as pydatetime

try:
    from urllib import urlencode
    from urllib2 import Request, urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

from scripts import base
from django.conf import settings

# # 云市场分配的密钥Id
# secretId = "AKID3V9sAthBknzLYgzHCVl5LNoCvlI5NmdrR7QZ"
# # 云市场分配的密钥Key
# secretKey = "275xj1sGHCcq7yXsIf7H6i9Tyv8t145thc2k8fRr"
def send_sms_single(mobile=None, code=None, template_id=None):

    # 云市场分配的密钥Id
    secretId = settings.TENCENT_SMS_APP_ID
    # 云市场分配的密钥Key
    secretKey = settings.TENCENT_SMS_APP_KEY
    source = "market"

    # 签名
    datetime = pydatetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    signStr = "x-date: %s\nx-source: %s" % (datetime, source)
    sign = base64.b64encode(hmac.new(secretKey.encode('utf-8'), signStr.encode('utf-8'), hashlib.sha1).digest())
    auth = 'hmac id="%s", algorithm="hmac-sha1", headers="x-date x-source", signature="%s"' % (
    secretId, sign.decode('utf-8'))

    # 请求方法
    method = 'GET'
    # 请求头
    headers = {
        'X-Source': source,
        'X-Date': datetime,
        'Authorization': auth,
    }
    # 查询参数
    # mobile    string   需要发送的手机号
    # param     string   模板中变量参数名,参数值,有多个时使用英文","隔开,例如:**验证码**:123455,**姓名**:张三
    # smsSignId string   签名ID，联系客服人员申请成功的签名ID。【测试请用：2e65b1bb3d054466b82f0c9d125465e2】
    # templateId  string  模板ID，联系客服人员申请成功的模板ID。【测试请用：f5e68c3ad6b6474faa8cd178b21d3377】

    code = template_id + code  # 使用tpl来区分是注册验证还是登录验证
    queryParams = {
        'mobile': mobile,
        'param': "**验证码**:{}".format(code),
        'smsSignId': '9be966cf25c14208bfa3a29a0273c2d5',
        'templateId': '092b0b4aadbf4531a447cc682e584956'}
    # body参数（POST方法下存在）
    bodyParams = {
    }
    # url参数拼接
    url = 'http://service-m6t5cido-1256923570.gz.apigw.tencentcs.com/release/sms/send'
    if len(queryParams.keys()) > 0:
        url = url + '?' + urlencode(queryParams)

    request = Request(url, headers=headers)
    request.get_method = lambda: method
    if method in ('POST', 'PUT', 'PATCH'):
        request.data = urlencode(bodyParams).encode('utf-8')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    response = urlopen(request, context=ctx)
    content = response.read().decode('utf-8')
    # if content:
    #     print(content)

    # {"msg":"成功","code":"0"}
    # {"msg":"验证未通过","code":"1905"}
    return content


if __name__ == '__main__':
    # 请求方式：GET
    # 返回类型：JSON
    content = send_sms_single(mobile='17864195254', code='20200805', template_id='11')
    if content:
        print(content)


