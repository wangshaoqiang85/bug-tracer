import json

data = {"name": "sunxiaomin", "sex": "nan", "age": "26"}
# 将python字典类型变成json数据格式
json_str = json.dumps(data)
print(json_str)
print(type(json_str))
# 将JSON数据解码为dict（字典）
data1 = json.loads(json_str)
print(data1)
print(type(data1))
print(data1['name'])
