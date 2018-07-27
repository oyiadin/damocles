# coding=utf-8

# superusers: 有权限执行所有命令的 QQ 号
# whitelist: 不对列表中的人进行关键词禁言、关键词回复、以及群名片检测
# forever_ban_list: 一发言就撤回消息并 30 天小黑屋伺候

host = '0.0.0.0'
port = 12000
connect_to = 'http://127.0.0.1:12100/'
access_token = ''
secret = ''

me = 10000
# 登录号（机器人号）
bugs_fixer = 10000
# 会把 traceback 私聊给这个 QQ 号
active_groups = (...)
# 启用的群号列表
