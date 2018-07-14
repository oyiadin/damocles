#coding=utf-8

import re
import sys
import requests
import traceback
from globals import *
from cqhttp import CQHttp

bot = CQHttp(api_root=connect_to, access_token=access_token, secret=secret)
superusers = list(map(int, open('superusers')))
whitelist = list(map(int, open('whitelist')))
blacklist = list(map(int, open('blacklist')))
blackhouselist = list(map(int, open('whitelist')))

def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            bot.send_private_msg(
                user_id=bugs_fixer,
                message='\n'.join(traceback.format_exception(*sys.exc_info())))
            # raise e
    return wrapper


@bot.on_message('private')
@handle_exception
def hdl_private_msg(cxt): #私聊
    groups = cxt['message'].strip().split()
    command = groups[0]
    if command == '%unban':
        if not cxt['user_id'] in superusers:
            return dict(reply=prompts['permission_needed'])
        if len(message) < 2:
            return dict(reply=prompts['need_more_arguments'])
        if not message[1].isdigit():
            return dict(reply=prompts['must_digits'])

        bot.set_group_whole_ban(
            group_id=int(message[1]), enable=False)
        return dict(reply=prompts['success_whole_unban'])

    elif command == '%debug_get_all_member':
        ret = bot.get_group_member_list(group_id=int(groups[1]))
        reply = []
        for i in ret:
            reply.append(str(i['user_id']) + ';' + i['card'] + ';' + i['nickname'])
        bot.send_private_msg(user_id=bugs_fixer, message='\n'.join(reply))
        return

    return dict(reply=prompts['private_preparing'])


@bot.on_message('group')
@handle_exception
def hdl_group_msg(cxt):#群成员消息
    if not cxt['group_id'] in active_groups:#不是被管理的群就不管
        return

    message = cxt['message'].strip()
    message_no_CQ = re.sub(R'\[CQ:[^\]]*\]', '', message)  # 排除 CQ 码

    if cxt['user_id'] in blackhouselist:#黑名单
        #TODO 撤回此人的消息
        return dict(
                    reply=prompts['black_house'],
                    ban=True, ban_duration=30 * 24 * 60 * 60)

    if not cxt['user_id'] in whitelist:#不在白名单中就进行回复和ban
        # 关键词ban
        for i in prohibited_words:
            if i in message_no_CQ:
                return dict(
                    reply=prompts['prohibited_occurred'],
                    ban=True, ban_duration=prohibited_duration*60)

        # 关键词回复
        for item in auto_reply:
            flag = False
            for i in item[0]:
                if i in message_no_CQ:
                    flag = True
                    break
            if flag:
                for i in item[1]:
                    if i in message_no_CQ:
                        return dict(reply=item[2])

    at_me = '[CQ:at,qq=%d]' % me#机器人被@
    if at_me in message:
        return dict(reply=prompts['why_at_me'], at_sender=False)

    # 命令执行
    if message == 'ping':#ping命令
        return dict(reply=prompts['ping'], at_sender=False)

    if not (message and message[0] == '%'):#不是命令就返回
        return

    groups = re.split(R' +', message)#命令各部分以空格拆分

    command = groups[0].lower()[1:]#去掉%号
    if cxt['user_id'] not in superusers and command in permission_commands:#非管理员使用受限命令
        return dict(reply=prompts['permission_needed'])

    if command == 's':
        return dict(reply=prompts['fmtstr_s'])
    
    if command == 'x':
        return dict(reply=prompts['fmtstr_x'])

    if command[-1] == 'n':
        result = re.match(r"\d?n")
        if result:
            return dict(reply=prompts['fmtstr_n'])
        else:
            return dict(reply=prompts['unknown_command'])         


    if command == 'ban' or command == 'unban':
        if len(groups) == 1:#全体命令
            if command == 'ban':
                bot.set_group_whole_ban(group_id=cxt['group_id'])
                return dict(reply=prompts['success_whole_ban'])
            else:
                bot.set_group_whole_ban(
                    group_id=cxt['group_id'], enable=False)
                return dict(reply=prompts['success_whole_unban'])
        #以下为对个人的操作
        if groups[1].isdigit():#第一操作数是数字
            qq = groups[1]
        else:
            match = re.match(R'\[CQ:at,qq=(\d+)\]', groups[1])
            if not match:
                return dict(reply=prompts['must_digits_or_CQat'])
            qq = int(match.group(1))

        if command == 'ban':
            if len(groups) >= 3 and not groups[2].isdigit():
                return dict(reply=prompts['must_digits'])
            duration = 2 if len(groups) < 3 else int(groups[2])
        else: #解禁就是把ban的时间设为零
            duration = 0

        bot.set_group_ban(
            group_id=cxt['group_id'], user_id=qq, duration=60*duration)
        return dict(
            reply=prompts['success_%s' % command].format(
                to=qq, duration=duration),
            at_sender=True)

    elif command == 'autocheck' or command == 'autokick':
        is_public = True #默认为公开的
        if len(groups) == 2:
            if groups[1] == 'public':
                is_public = True
            elif groups[1] == 'private':
                is_public = False
            else:
                return dict(reply=prompts['wrong_argument'])

        ret = bot.get_group_member_list(group_id=cxt['group_id'])
        for i in ret:
            if i['user_id'] in whitelist or i['role'] in ('admin', 'owner'):#白名单 群主 管理 除外
                continue
            if not re.match(card_pattern, i['card']):
                at = '[CQ:at,qq=%d] ' % i['user_id']
                if command == 'autocheck':
                    if is_public:
                        bot.send(cxt, at + prompts['request_change_card'])
                    else:
                        bot.send_private_msg(
                            user_id=i['user_id'],
                            message=prompts['request_change_card'])
                else:
                    bot.set_group_kick(
                        group_id=cxt['group_id'], user_id=i['user_id'])
                    bot.send_private_msg(
                        user_id=i['user_id'],
                        message=prompts['kick_for_card_incorrect'])#踢人后申明

        return dict(reply=prompts['success_auto_check_card'])

    elif command == 'help' or command == 'menu':
        return dict(reply=prompts['menu'])

    elif command == 'ping':
        return dict(reply=prompts['ping'], at_sender=False)

    else:
        return dict(reply=prompts['unknown_command'])


@bot.on_notice('group_increase')
@handle_exception
def handle_group_increase(cxt):
    at = '[CQ:at,qq=%d] ' % cxt['user_id']
    bot.send_group_msg(**cxt, message=at+prompts['welcome_newbie'])


@bot.on_request('friend')
@handle_exception
def handle_request(cxt):
    return dict(approve=True)


@bot.on_request('group')
@handle_exception
def handle_request(cxt):
    # 加群邀请直接同意
    if cxt['sub_type'] == 'invite' and cxt['group_id'] in active_groups:
        return dict(approve=True)

    if not enable_group_in_auto_check:
        return
    if not cxt['group_id'] in active_groups:
        return

    if cxt['user_id'] in blacklist:#黑名单成员会被禁止加入
        return dict(approve=false)//TODO 我不确定拒绝是否这样写

    match = re.match(
        R"(\d+)[\s\-\.\+]*(\w+)",
        (cxt['comment'].split('答案：') or ['', ''])[1].strip())
    if not match:
        # return dict(approve=False, reason=prompts['group_request_plz_fill'])
        return

    id, name = match.groups()
    ret = requests.get(info_check_url.format(id)).json()
    if ret.get('name') != name:
        # return dict(approve=False, reason=prompts['group_request_plz_correct'])
        return
    else:
        return dict(approve=True)


bot.run(host=host, port=port)
