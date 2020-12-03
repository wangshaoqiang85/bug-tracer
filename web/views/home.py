import datetime
import time
import json
from django.shortcuts import render, redirect, reverse
from django.conf import settings
from django.http import HttpResponse
from django_redis import get_redis_connection
from utils.encrypt import uid
from utils.alipay import AliPay
from web import models


def index(request):
    """首页"""
    return render(request, 'web/index.html')


def price(request):
    """价格策略"""
    policy_list = models.PricePolicy.objects.filter(category=2).all()
    return render(request, 'web/price.html', {'policy_list': policy_list})


def payment(request, policy_id):
    """订单"""
    # 1、判断价格策略是否存在
    policy_object = models.PricePolicy.objects.get(id=policy_id)
    if not policy_object:
        return redirect(reverse('web:price'))

    # 2、要购买的数量
    number = request.GET.get('number')
    if not number or not number.isdecimal():
        return redirect(reverse('web:price'))

    # 3、计算原价
    origin_price = int(number) * policy_object.price

    # 4、之前购买过套餐，可以做折扣
    # request.tracer.price_policy.category 是在中间中找到当前登录用户的最大额度
    # 如果当前用户的最大额度是收费版的，就做抵扣
    balance = 0
    _object = None
    if request.tracer.price_policy.category == 2:
        _object = models.Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-id').first()
        # 计算抵扣，需要总支付费用，开始-结束时间，剩余天数
        total_timedelta = _object.end_datetime - _object.start_datetime  # 付费版总共多少天
        balance_timedelta = _object.end_datetime - datetime.datetime.now()  # 还剩余多少天
        if total_timedelta.days == balance_timedelta.days:
            balance = _object.price / total_timedelta.days * (balance_timedelta.days - 1)
        else:
            balance = _object.price / total_timedelta.days * balance_timedelta.days

    if balance >= origin_price:
        return redirect(reverse('web:price'))

    context = {
        'policy_id': policy_object.id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance, 2),
        'total_price': round(origin_price - balance, 2)
        # 'total_price': round(origin_price, 2) - round(balance, 2)
    }

    # 将交易信息添加到redis数据库中
    conn = get_redis_connection('default')
    key = 'payment_{}'.format(request.tracer.user.mobile_phone)
    conn.set(key, json.dumps(context), ex=60 * 30)

    context['policy_object'] = policy_object
    context['transaction'] = _object

    return render(request, 'web/payment.html', context)


def pay(request):
    """生成订单 并且 实现支付宝支付"""

    conn = get_redis_connection('default')
    key = 'payment_{}'.format(request.tracer.user.mobile_phone)
    context_string = conn.get(key)
    if not context_string:
        return redirect(reverse('web:price'))
    context = json.loads(context_string.decode('utf-8'))

    # 1、数据库中生成交易记录, 应该是未支付状态
    #   支付成功之后，需要把订单的状态更新为以及支付， 设置开始和结束时间
    # 先创建订单编号
    time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))  # 时间戳格式化
    order_id = time_str + uid(request.tracer.user.mobile_phone)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price
    )

    # 2、生成支付链接
    # 生成支付链接

    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = ali_pay.direct_pay(
        subject="tracer payment",  # 商品简单描述
        out_trade_no=order_id,  # 商户订单号
        total_amount=total_price
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)


def pay_notify(request):
    """支付宝支付成功之后触发的URL"""
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    if request.method == 'GET':
        # 只做跳转，判断是否支付成功了，不做订单的状态更新。
        # 支付宝会将订单号返回：获取订单ID，然后根据订单ID做状态更新 + 认证。
        # 支付宝公钥对支付后返回的数据request.GET 进行检查，通过则表示这是支付宝返还的接口。
        params = request.GET.dict()
        sign = params.pop('sign', None)
        print(sign)
        status = ali_pay.verify(params, sign)

        current_datetime = datetime.datetime.now()
        out_trade_no = params['out_trade_no']
        _object = models.Transaction.objects.filter(order=out_trade_no).first()

        _object.status = 2
        _object.start_datetime = current_datetime
        _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
        _object.save()

        # return HttpResponse('支付完成')
        return redirect(reverse('web:price'))
        # if status:
        #     return HttpResponse('支付失败')

    if request.method == 'POST':
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()

            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=_object.count * 365)
            _object.save()
            return HttpResponse('success')
        return HttpResponse('error')
