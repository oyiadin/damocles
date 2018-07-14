#coding=utf-8

# superusers: 有权限执行所有命令的 QQ 号
# whitelist: 不对列表中的人进行关键词禁言、关键词回复、以及群名片检测
# 
host = '0.0.0.0'
port = 8080
connect_to = 'http://127.0.0.1:5700/'
access_token = ''
secret = ''

me = 10000
# 登录号（机器人号）
bugs_fixer = 10000
# 会把 traceback 私聊给这个 QQ 号
active_groups = []
# 启用的群号列表

enable_group_in_auto_check = True
# 如果为真，会自动将学号姓名正确的批准加群
card_pattern = R"\d{2}[\- ]+\w+[\- ]+\w+"
# 群名片 pattern

auto_reply = [
    [
        ["key1", "key2"],
        ["key3", "key4", "key5"],
        "回复内容"
    ],
    # ...
]
# 自动回复的检测分为两组关键词，如果两组关键词均至少出现一个，则回复之

prohibited_words = ["女装", "膜"]
prohibited_duration = 2

prompts = dict(
    ping = 'pong!',
    why_at_me = '@我干嘛？',
    prohibited_occurred = '本群禁膜禁女装，给你两分钟冷静冷静~',
    unknown_command = '未知命令，请输入%help或%menu查看命令',
    need_more_arguments = '缺少必要参数',
    must_digits_or_CQat = '参数必须是 QQ 号或者一次成功的 @人',
    must_digits = '参数必须是正整数',
    wrong_argument = '参数错误',
    permission_needed = '你没有执行此命令的权限',
    group_request_plz_fill = '必须完整填写你的学号姓名',
    group_request_plz_correct = '请正确填写你的学号姓名',
    request_change_card = '你的群名片不符合规范，请修改',
    kick_for_card_incorrect = '由于你的群名片不符合规范，你已被移出群\n'
                              '因为群昵称更新的频率很低，误判也不是不可能\n'
                              '如果因此对你进行了误操作，十分抱歉，重新加群即可~',
    success_ban = '禁言成功，[CQ:at,qq={to}] 将被禁言 {duration} 分钟',
    success_whole_ban = '已开启全员禁言，有权限的人可私聊回复 /unban 群号 解除全员禁言',
    success_unban = '解禁成功，对 [CQ:at,qq={to}] 的禁言已被撤销',
    success_whole_unban = '全员禁言已关闭',
    success_auto_check_card = '群名片检查完毕',
    private_preparing = '私聊模块还没想好写什么功能',
    menu = '\n'.join(['支持以下命令',
                      '/ban* [QQ/@] [分钟]',
                      '禁言，默认2min，省略QQ则全员禁言',
                      '/unban* [QQ/@]',
                      '解除禁言，省略QQ则关闭全员禁言',
                      '/autocheck* [to] 与 /autokick*',
                      '检测群名片规范与否，前者@人提醒，后者直接踢人',
                      '慎用，因为群名片很久才会更新一次',
                      'to参数可填public或private，即群里或私聊提醒，默认群里',
                      '/menu /ping',
                      '懒得解释\n',
                      '标*号者需要权限']),
    welcome_newbie = "Hi，欢迎加入本群~",
    black_house = "你已被永久禁言，麻烦私聊管理员询问具体事项",
    fmtstr_s = "flag{welcome_to_vidar}烫烫烫烫烫",
    fmtstr_x = "66",#上文对应666C61677B77656C636F6D655F746F5F76696461727DCCCCCCCCCCCCCCCCCCCC
    fmtstr_n = "别嘛，再这样我就生气了"
)

permission_commands = ["ban", "unban", "autocheck", "autokick"]

info_check_url = 'http://example.com/api/student/info/{}'
