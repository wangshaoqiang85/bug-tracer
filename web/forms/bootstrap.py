# 给表单字段添加样式的基类
class BootstrapForm(object):
    # 自定义一个列表，如果字段在其中，则不使用bootstrap样式
    bootstrap_class_exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, ** kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_class_exclude:
                continue

            old_class = field.widget.attrs.get('class', '')
            # 给表单添加样式
            field.widget.attrs['class'] = '{} form-control'.format(old_class)
            field.widget.attrs['placeholder'] = '请输入{}'.format(field.label)

#
# class Foo(BootStrapForm):
#     pass
#
# obj = Foo()