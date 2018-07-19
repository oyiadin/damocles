import re
import subprocess
from globals import *
from base import *
import sqli


@bot.register(public=True)
@handle_exception
def forever_ban(cxt):
    if cxt['user_id'] in forever_ban_list:
        bot.delete_msg(message_id=cxt['message_id'])
        bot.send_private_msg(
            user_id=cxt['user_id'], message=prompts['forever_ban_private'])
        return dict(
            reply=prompts['black_house'], ban=True, ban_duration=43200)
        # 一旦发言，撤回并重新禁言 30 天


@bot.register(public=True)
@handle_exception
def keyword_ban(cxt):
    # 白名单内的人不进行关键词 ban
    if not cxt['user_id'] in whitelist:
        # 关键词ban
        for i in prohibited_words:
            if i in cxt['message_no_CQ']:
                return dict(
                    reply=prompts['prohibited_occurred'],
                    ban=True, ban_duration=prohibited_duration * 60)


@bot.register(public=True)
@handle_exception
def keyword_autoreply(cxt):
    # 关键词回复
    # 无视白名单，因为有时候想刻意触发
    for item in auto_reply:
        flag = False
        for i in item[0]:
            if i in cxt['message_no_CQ']:
                flag = True
                break
        if flag:
            for i in item[1]:
                if i in cxt['message_no_CQ']:
                    return dict(reply=item[2])


@bot.register(public=True)
@handle_exception
def at_me_handler(cxt):
    at_me = '[CQ:at,qq=%d]' % me  # 机器人被@
    if at_me in cxt['message']:
        return dict(reply=prompts['why_at_me'], at_sender=False)


@bot.register('ban', public=True)
@bot.register('unban', public=True)
@handle_exception
def cmd_ban_unban_public(cxt):
    groups = cxt['groups']
    command = cxt['command']
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
        group_id=cxt['group_id'], user_id=qq, duration=60 * duration)
    return dict(
        reply=prompts['success_%s' % command].format(
            to=qq, duration=duration),
        at_sender=True)


@bot.register('unban', private=True)
@handle_exception
def cmd_unban_private(cxt):
    groups = cxt['groups']
    if len(groups) < 2:
        return dict(reply=prompts['need_more_arguments'])
    if not groups[1].isdigit():
        return dict(reply=prompts['must_digits'])

    bot.set_group_whole_ban(
        group_id=int(groups[1]), enable=False)
    return dict(reply=prompts['success_whole_unban'])


@bot.register('autocheck', public=True)
@bot.register('autokick', public=True)
@handle_exception
def cmd_autocheck_autokick(cxt):
    is_public = True
    groups = cxt['groups']
    command = cxt['command']
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


@bot.register('printf', public=True, private=True)
@handle_exception
def cmd_printf(cxt):
    groups = cxt['groups']
    remains = cxt['message_no_CQ'][8:]  # 截掉`%printf `
    if len(groups) < 2:
        return dict(reply=prompts['need_more_arguments'])

    f = subprocess.Popen(
        './fmtstr', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        ret = f.communicate(remains.encode('utf-8'), timeout=0.8)[0]
        assert ret
        return dict(reply=ret.decode('utf-8'), at_sender=False)
    except (subprocess.TimeoutExpired, AssertionError):
        return dict(reply=prompts['printf_crash'])


@bot.register('bonus', public=True, private=True)
@handle_exception
def sqli(cxt):
    groups = cxt['groups']
    cmd = cxt['message_no_CQ'].split(' ').pop(0)
    if cmd[0] == 'init':
        sqli.init()
    elif cmd[0] == 'create':
        if sqli.createActivationCode(cmd[1]):
            return dict(reply='%s个激活码生成完毕' % cmd[1])
    elif cmd[0] == 'show':
        return sqli.getActivationCode()
    else:
        return sqli.getBonus(cxt['user_id'], cmd[1])
    if len(groups) < 2:
        return dict(reply=prompts['need_more_arguments'])


@bot.register('help', public=True)
@bot.register('menu', public=True)
@handle_exception
def cmd_menu(cxt):
    return dict(reply=prompts['menu'])


@bot.register('ping', public=True, private=True)
@handle_exception
def cmd_ping(cxt):
    return dict(reply=prompts['ping'], at_sender=False)


@bot.register('debug_get_all_member', private=True)
@handle_exception
def cmd_debug_get_all_member(cxt):
    groups = cxt['groups']
    ret = bot.get_group_member_list(group_id=int(groups[1]))
    reply = []
    for i in ret:
        reply.append(str(i['user_id']) + ';' + i['card'] + ';' + i['nickname'])
    bot.send_private_msg(user_id=bugs_fixer, message='\n'.join(reply))


if __name__ == '__main__':
    bot.run(host=host, port=port)
