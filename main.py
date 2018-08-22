import re
import sqli
import gal
import subprocess
import html.parser
from base import *
from globals import *
from keywords import check_if_exist, if_any_autoreply


@bot.register(public=True)
def forever_ban(cxt):
    if cxt['user_id'] in forever_ban_list:
        # bot.delete_msg(message_id=cxt['message_id'])
        bot.send_private_msg(
            user_id=cxt['user_id'], message=prompts['forever_ban_private'])
        return dict(
            reply=prompts['black_house'], ban=True, ban_duration=43200)
        # 一旦发言，撤回并重新禁言 30 天
        # 酷 Q Air 不支持撤回…


@bot.register(public=True)
def keyword_ban(cxt):
    # 白名单内的人不进行关键词 ban
    do_ban_keys = ['dress', 'admire', 'violation', 'dirty']
    if not cxt['user_id'] in whitelist:
        for key in do_ban_keys:
            reply = check_if_exist(key, cxt['message_no_CQ'])
            if reply:
                duration = 60 * 60 * 24 * 2 if key == 'dirty' \
                    else prohibited_duration * 60
                # 脏话直接禁两天
                return dict(
                    reply=reply, ban=True, ban_duration=duration)


@bot.register(public=True)
def ban_if_code(cxt):
    keys = [
        '#include', 'main(', 'printf(', 'std::', 'In file included from', 'required from',
        'return', 'for', 'while'
    ]
    if len(cxt['message']) > 150 and cxt['user_id'] not in whitelist:
        for i in keys:
            if i in cxt['message']:
                # bot.delete_msg(message_id=cxt['message_id'])
                return dict(reply=prompts['code_too_long'], ban=True, ban_duration=60)


@bot.register(public=True)
def ban_if_too_long(cxt):
    if len(cxt['message']) > 1000 and cxt['user_id'] not in whitelist:
        return dict(reply=prompts['msg_too_long'], ban=True, ban_duration=120)


@bot.register(public=True)
def keyword_autoreply(cxt):
    # 关键词回复
    # 无视白名单，因为有时候想刻意触发
    reply = if_any_autoreply(cxt['message_no_CQ'])
    if reply:
        return dict(reply=reply)


@bot.register(public=True)
def at_me_handler(cxt):
    at_me = '[CQ:at,qq=%d]' % cli_args.qq  # 机器人被@
    if at_me in cxt['message']:
        return dict(reply=prompts['why_at_me'], at_sender=False)


@bot.register('ban', public=True)
@bot.register('unban', public=True)
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


@bot.register('ban', private=True)
@bot.register('unban', private=True)
def cmd_ban_unban_private(cxt):
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
            bot.set_group_whole_ban(group_id=private_ban_group)
            return dict(reply=prompts['success_whole_ban'])
        else:
            bot.set_group_whole_ban(
                group_id=private_ban_group, enable=False)
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
        group_id=private_ban_group, user_id=qq, duration=60 * duration)
    return dict(
        reply=prompts['success_%s' % command].format(
            to=qq, duration=duration),
        at_sender=False)


@bot.register('autocheck', public=True)
@bot.register('autokick', public=True)
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
        how_many_groups = len(ats) // 50
        if len(ats) % 50:
            how_many_groups += 1
        import time
        for i in range(how_many_groups):
            bot.send(cxt,
                     message=' '.join(ats[50 * i:50 * (i + 1)]) + '\n' + prompts['request_change_card'],
                     at_sender=False)
            time.sleep(2)  # 先强行阻塞，有时间再改成子线程

    return dict(reply=prompts['success_auto_check_card'])


@bot.register('printf', public=True, private=True)
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


@bot.register('shellcode', public=True, private=True)
def cmd_printf(cxt):
    groups = cxt['groups']
    remains = cxt['message_no_CQ'][11:]  # 截掉`%shellcode `
    remains = html.parser.HTMLParser().unescape(remains)
    f = subprocess.Popen(
        ['./playshellcode',str(cxt['user_id'])], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        if len(groups) < 2:
            ret = f.communicate('help'.encode('utf-8'), timeout=2)[0]
            return dict(reply=ret.decode('utf-8'), at_sender=False)
        ret = f.communicate(remains.encode('utf-8'), timeout=2)[0]
        retcode = f.wait()
        if(retcode < 0):
            return dict(reply=prompts['shellcode_crash'])
        elif(retcode == 0):
            return dict(reply=ret.decode('utf-8'), at_sender=False)
        assert ret
        return dict(reply=ret.decode('utf-8'), at_sender=False)
    except (subprocess.TimeoutExpired, AssertionError):
        return dict(reply=prompts['shellcode_crash'])


@bot.register('bonus', public=True, private=True)
def sqli_handle(cxt):
    groups = cxt['groups']
    if len(groups) < 2:
        return dict(reply=prompts['need_more_arguments'])
    groups.pop(0)
    if groups[0] == 'init':
        sqli.init()
    elif groups[0] == 'create':
        if not groups[1].isdigit():
            return dict(reply=prompts['must_digits'])
        return sqli.createActivationCode(int(groups[1]))
    elif groups[0] == 'show':
        return sqli.getActivationCode()
    elif groups[0] == 'help':
        return dict(reply=prompts['bonus_help'])
    else:
        return sqli.getBonus(cxt['user_id'], groups[0])


@bot.register('gal', public=True, private=True)
def galstart_handle(cxt):
    if not cxt.get('group_id') or cxt.get('group_id') == cli_args.gal:
        return gal.startgame(cxt)
    else:
        return prompts['gal_not_here'].format(cli_args.gal)


@bot.register(public=True, private=True)
def galplay_handle(cxt):
    if not cxt.get('group_id') or cxt.get('group_id') == cli_args.gal:
        return gal.makechoice(cxt)


@bot.register('help', public=True)
@bot.register('menu', public=True)
def cmd_menu(cxt):
    return dict(reply=prompts['menu'])


@bot.register('ping', public=True, private=True)
def cmd_ping(cxt):
    return dict(reply=prompts['ping'], at_sender=False)


@bot.register('debug_get_all_member', private=True)
def cmd_debug_get_all_member(cxt):
    groups = cxt['groups']
    ret = bot.get_group_member_list(group_id=int(groups[1]))
    reply = []
    for i in ret:
        reply.append(str(i['user_id']) + ';' + i['card'] + ';' + i['nickname'])
    bot.send_private_msg(user_id=cli_args.bugs_fixer, message='\n'.join(reply))


if __name__ == '__main__':
    gal.scn_init()
    bot.run(host=cli_args.host, port=cli_args.port)
