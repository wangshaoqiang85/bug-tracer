import scripts.base

from web import models


def add_price_policy_free():
    exists = models.PricePolicy.objects.filter(category=1, title='个人免费版').exists()
    if not exists:
        models.PricePolicy.objects.create(
            category=1,
            title='个人免费版',
            price=0,
            project_num=3,
            project_member=2,
            project_space=20,
            per_file_size=5
        )
    else:
        print('已经存在')


def add_issues_comment():
    models.IssuesReply.objects.create(
        reply_type=2,
        content='我和你的意见差不多。',
        creator_id=2,
        issues_id=1,
        reply_id=2
    )


def add_price_policy():
    models.PricePolicy.objects.create(
        title='VIP',
        price=100,
        project_num=50,
        project_member=10,
        project_space=256,
        per_file_size=64,
        category=2
    )

    models.PricePolicy.objects.create(
        title='SVIP',
        price=200,
        project_num=120,
        project_member=30,
        project_space=512,
        per_file_size=128,
        category=2
    )

    models.PricePolicy.objects.create(
        title='SSVIP',
        price=500,
        project_num=300,
        project_member=100,
        project_space=1024,
        per_file_size=256,
        category=2
    )


if __name__ == '__main__':
    # add_price_policy_free()
    # add_issues_comment()
    add_price_policy()  # 收费版价格策略

