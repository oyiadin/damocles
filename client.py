#coding=utf-8

import re
import sys
import ctypes
import requests
import traceback
from globals import *
from cqhttp import CQHttp

libc = ctypes.CDLL('libc.so.6')
bot = CQHttp(api_root=connect_to, access_token=access_token, secret=secret)
superusers = list(map(int, open('superusers')))
whitelist = list(map(int, open('whitelist')))
forever_ban_list = list(map(int, open('forever_ban_list')))

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
def hdl_private_msg(cxt):
    groups = cxt['message'].strip().split()
    command = groups[0]
    if command == '%unban':
        if not cxt['user_id'] in superusers:
            return dict(reply=prompts['permission_needed'])
        if len(groups) < 2:
            return dict(reply=prompts['need_more_arguments'])
        if not groups[1].isdigit():
            return dict(reply=prompts['must_digits'])

        bot.set_group_whole_ban(
            group_id=int(groups[1]), enable=False)
        return dict(reply=prompts['success_whole_unban'])

    elif command == '%debug_get_all_member':
        if not cxt['user_id'] in superusers:
            return dict(reply=prompts['permission_needed'])
        ret = bot.get_group_member_list(group_id=int(groups[1]))
        reply = []
        for i in ret:
            reply.append(str(i['user_id']) + ';' + i['card'] + ';' + i['nickname'])
        bot.send_private_msg(user_id=bugs_fixer, message='\n'.join(reply))
        return

    elif command == '%printf':
        remains = cxt['message'].strip()[8:]
        if len(groups) < 2:
            return dict(reply=prompts['need_more_arguments'])
        if 'n' in remains:
            return dict(reply='no `n` plz')

        buf = ctypes.c_buffer(1000)
        libc.sprintf(buf, remains.encode('utf-8'), *fmtstr_args)
        # 直接拿没经过处理的用户输入，截掉命令
        return dict(reply=str(buf.value.decode('utf-8')))

    return dict(reply=prompts['private_preparing'])


@bot.on_message('group')
@handle_exception
def hdl_group_msg(cxt):
    if not cxt['group_id'] in active_groups:  # 不是被管理的群就不管
        return

    message = cxt['message'].strip()
    message_no_CQ = re.sub(R'\[CQ:[^\]]*\]', '', message)  # 排除 CQ 码

    if cxt['user_id'] in forever_ban_list:
        bot.delete_msg(message_id=cxt['message_id'])
        bot.send_private_msg(
            user_id=cxt['user_id'], message=prompts['forever_ban_private'])
        return dict(
            reply=prompts['black_house'], ban=True, ban_duration=43200)
        # 一旦发言，撤回并重新禁言 30 天

    # 白名单内的人不进行关键词 ban
    if not cxt['user_id'] in whitelist:
        # 关键词ban
        for i in prohibited_words:
            if i in message_no_CQ:
                return dict(
                    reply=prompts['prohibited_occurred'],
                    ban=True, ban_duration=prohibited_duration*60)

    # 关键词回复
    # 无视白名单，因为有时候想刻意触发
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

    at_me = '[CQ:at,qq=%d]' % me  # 机器人被@
    if at_me in message:
        return dict(reply=prompts['why_at_me'], at_sender=False)

    # 命令执行
    # 单独处理 ping，无须 %ping
    if message == 'ping':
        return dict(reply=prompts['ping'], at_sender=False)

    if not (message and message[0] == '%'):
        return

    groups = re.split(R' +', message)
    # 命令各部分以空格拆分
    command = groups[0].lower()[1:]  # 去掉 % 号
    if cxt['user_id'] not in superusers and command in permission_commands:
        return dict(reply=prompts['permission_needed'])

    if command == 'ban' or command == 'unban':
        if len(groups) < 2:
            return dict(reply=prompts['need_more_arguments'])

        # QQ 号
        if groups[1].isdigit():
            qq = groups[1]

        # 全员禁言，处理完直接 return
        elif groups[1].lower() == 'all':
            if command == 'ban':
                bot.set_group_whole_ban(group_id=cxt['group_id'])
                return dict(reply=prompts['success_whole_ban'])
            else:
                bot.set_group_whole_ban(
                    group_id=cxt['group_id'], enable=False)
                return dict(reply=prompts['success_whole_unban'])

        # CQ 码 @ 或错误参数
        else:
            match = re.match(R'\[CQ:at,qq=(\d+)\]', groups[1])
            if not match:
                return dict(reply=prompts['must_digits_or_CQat'])
            qq = int(match.group(1))

        if command == 'ban':
            if len(groups) >= 3 and not groups[2].isdigit():
                return dict(reply=prompts['must_digits'])
            duration = 2 if len(groups) < 3 else int(groups[2])
        else:  # duration = 0 就是解禁
            duration = 0

        bot.set_group_ban(
            group_id=cxt['group_id'], user_id=qq, duration=60*duration)
        return dict(
            reply=prompts['success_%s' % command].format(
                to=qq, duration=duration),
            at_sender=True)

    elif command == 'autocheck' or command == 'autokick':
        is_public = False
        if len(groups) == 2:
            if groups[1].lower() == 'public':
                is_public = True
            elif groups[1].lower() == 'private':
                is_public = False
            else:
                return dict(reply=prompts['wrong_argument'])

        ret = bot.get_group_member_list(group_id=cxt['group_id'])
        ats = []

        for i in ret:
            if i['user_id'] in whitelist or i['role'] in ('admin', 'owner'):
                continue
                # 不检查白名单、群主、管理

            if not re.match(card_pattern, i['card']):
                at = '[CQ:at,qq=%d]' % i['user_id']
                if command == 'autocheck':
                    if is_public:
                        ats.append(at)
                    else:
                        bot.send_private_msg(
                            user_id=i['user_id'],
                            message=prompts['request_change_card'])
                else:
                    bot.send_private_msg(
                        user_id=i['user_id'],
                        message=prompts['kick_for_card_incorrect'])
                    # 踢人前私聊提醒
                    # 不过没加好友的话发不出去，没有临时会话的 API
                    bot.set_group_kick(
                        group_id=cxt['group_id'], user_id=i['user_id'])
        if ats:
            bot.send(cxt,
                message=' '.join(ats) + '\n' + prompts['request_change_card'],
                at_sender=False)

        return dict(reply=prompts['success_auto_check_card'])

    elif command == 'printf':
        remains = cxt['message'].strip()[8:]
        if len(groups) < 2:
            return dict(reply=prompts['need_more_arguments'])
        if 'n' in remains:
            return dict(reply='no `n` plz')

        buf = ctypes.c_buffer(1000)
        libc.sprintf(buf, remains.encode('utf-8'), *fmtstr_args)
        # 直接拿没经过处理的用户输入，截掉命令
        return dict(reply=str(buf.value.decode('utf-8')), at_sender=False)

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
    # 好友申请直接同意
    return dict(approve=True)


@bot.on_request('group')
@handle_exception
def handle_request(cxt):
    # 如果该群没有开启功能，无论是啥都不管
    if not cxt['group_id'] in active_groups:
        return

    # 加群邀请直接同意
    if cxt['sub_type'] == 'invite':
        return dict(approve=True)
    if not enable_group_in_auto_check:
        return

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
