#coding=utf-8
import re
import sys
import argparse
import requests
import traceback
from globals import *
from config import *
from cqhttp import CQHttp


parser = argparse.ArgumentParser()
parser.add_argument('--host', default=host)
parser.add_argument('-p', '--port', type=int, default=port)
parser.add_argument('-c', '--connect_to', default=connect_to)
parser.add_argument('-t', '--access_token', default=access_token)
parser.add_argument('-s', '--secret', default=secret)
parser.add_argument('-q', '--qq', type=int, default=me)
parser.add_argument('-b', '--bugs_fixer', type=int, default=bugs_fixer)
parser.add_argument('-g', '--active_groups',
    type=int, nargs='*', default=active_groups)
parser.add_argument('--no_whitelist', action='store_true')
cli_args = parser.parse_args()


def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            bot.send_private_msg(
                user_id=cli_args.bugs_fixer,
                message='\n'.join(traceback.format_exception(*sys.exc_info())))
            # raise e
    return wrapper


class BaseHandler(CQHttp):
    def __init__(self, *args, **kwargs):
        self.commands = [{}, {}]   # 只处理对应命令
        self.functions = [[], []]  # 所有消息都会经这里处理
        # 0-私聊; 1-群组
        super().__init__(*args, **kwargs)

    def register(self, command=None, private=False, public=False):
        def decorator(func):
            if command:
                if private:
                    self.commands[0][command] = func
                if public:
                    self.commands[1][command] = func
            else:
                if private:
                    self.functions[0].append(func)
                if public:
                    self.functions[1].append(func)
            return func
        return decorator


bot = BaseHandler(
    api_root=cli_args.connect_to,
    access_token=cli_args.access_token,
    secret=cli_args.secret)
superusers = list(map(int, open('superusers')))
whitelist = list(map(int, open('whitelist'))) \
    if not cli_args.no_whitelist else []
forever_ban_list = list(map(int, open('forever_ban_list')))


def unknown_command(cxt):
    return dict(reply=prompts['unknown_command'])


@bot.on_message('private', 'group')
@handle_exception
def hdl_msg(cxt):
    is_group = bool(cxt.get('group_id'))
    if is_group and not cxt['group_id'] in cli_args.active_groups:  # 不是被管理的群就不管
        return

    cxt['message'] = cxt['message'].strip()
    cxt['message_no_CQ'] = re.sub(R'\[CQ:[^\]]*\]', '', cxt['message'])
    # 排除 CQ 码

    for func in bot.functions[is_group]:
        ret = func(cxt)
        if ret:
            return ret

    if not (cxt['message'] and cxt['message'][0] == '%'):
        return
    cxt['groups'] = re.split(R' +', cxt['message'])  # 命令各部分以空格拆分
    cxt['command'] = cxt['groups'][0].lower()[1:]    # 去掉 % 号

    if cxt['user_id'] not in superusers \
        and cxt['command'] in permission_commands:
            return dict(reply=prompts['permission_needed'])

    return bot.commands[is_group].get(cxt['command'], unknown_command)(cxt)


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
    if not cxt['group_id'] in cli_args.active_groups:
        return

    # 加群邀请直接同意
    if cxt['sub_type'] == 'invite':
        return dict(approve=True)
    if not enable_group_in_auto_check:
        return

    if '答案：' in cxt['comment']:
        match = re.match(
            R"(\d+)[\s\-\.\+]*(\w+)",
            (cxt['comment'].split('答案：'))[1].strip())
        if not match:
            # return dict(approve=False, reason=prompts['group_request_plz_fill'])
            return

        id, name = match.groups()
        ret = requests.get(info_check_url.format(id)).json()
        if ret.get('name') == name:
            return dict(approve=True)
        else:
            # return dict(approve=False, reason=prompts['group_request_plz_correct'])
            return
