#coding=utf-8

import re
import sys
import requests
import traceback
from globals import *
from cqhttp import CQHttp

bot = CQHttp(api_root=connect_to)
superusers = list(map(int, open('superusers')))
whitelist = list(map(int, open('whitelist')))


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
    message = cxt['message'].strip().split()
    if message[0] == '/unban':
        if not cxt['user_id'] in superusers:
            return dict(reply=prompts['permission_needed'])
        if len(message) < 2:
            return dict(reply=prompts['need_more_arguments'])
        if not message[1].isdigit():
            return dict(reply=prompts['must_digits'])

        bot.set_group_whole_ban(
            group_id=int(message[1]), enable=False)
        return dict(reply=prompts['success_whole_unban'])

    return dict(reply=prompts['private_preparing'])


@bot.on_message('group')
@handle_exception
def hdl_group_msg(cxt):
    if not cxt['group_id'] in active_groups:
        return
    message = cxt['message'].strip()

    if not cxt['user_id'] in whitelist:
        # 关键词ban
        for i in prohibited_words:
            if i in message:
                return dict(
                    reply=prompts['prohibited_occurred'],
                    ban=True, ban_duration=prohibited_duration*60)

        # 关键词回复
        for item in auto_reply:
            flag = False
            for i in item[0]:
                if i in message:
                    flag = True
                    break
            if flag:
                for i in item[1]:
                    if i in message:
                        return dict(reply=item[2])

    at_me = '[CQ:at,qq=%d]' % me
    if at_me in message:
        return dict(reply=prompts['why_at_me'])

    # 命令执行
    if message == 'ping':
        return dict(reply=prompts['ping'], at_sender=False)
    if not (message and message[0] == '/'):
        return
    groups = re.split(R' +', message)
    command = groups[0].lower()[1:]
    if cxt['user_id'] not in superusers and command in permission_commands:
        return dict(reply=prompts['permission_needed'])

    if command == 'ban' or command == 'unban':
        if len(groups) == 1:
            if command == 'ban':
                bot.set_group_whole_ban(group_id=cxt['group_id'])
                return dict(reply=prompts['success_whole_ban'])
            else:
                bot.set_group_whole_ban(
                    group_id=cxt['group_id'], enable=False)
                return dict(reply=prompts['success_whole_unban'])

        if groups[1].isdigit():
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
        else:
            duration = 0

        bot.set_group_ban(
            group_id=cxt['group_id'], user_id=qq, duration=60*duration)
        return dict(
            reply=prompts['success_%s' % command].format(
                to=qq, duration=duration),
            at_sender=True)

    elif command == 'autocheck' or command == 'autokick':
        is_public = True
        if len(groups) == 2:
            if groups[1] == 'public':
                is_public = True
            elif groups[1] == 'private':
                is_public = False
            else:
                return dict(reply=prompts['wrong_argument'])

        ret = bot.get_group_member_list(group_id=cxt['group_id'])
        for i in ret:
            if i['user_id'] in whitelist or i['role'] in ('admin', 'owner'):
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
                        message=prompts['kick_for_card_incorrect'])

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
    if not enable_group_in_auto_check:
        return
    if not cxt['group_id'] in active_groups:
        return

    match = re.match(
        R"(\d+)[\s\-\.\+]*(\w+)",
        cxt['comment'].split('答案：')[1].strip())
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
