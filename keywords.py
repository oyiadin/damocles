# coding=utf-8
import random

chains = {}
replies = {}
silence = {}

dress1 = ('有', '给', '去', '穿', '买', '奖')
dress2 = ('女装', 'rbq')
admire1 = ('膜', '摸', '%', 'mo')
admire2 = ('群主', '管理员', '你', '大佬', 'dalao')
chains['dress'] = (
    (dress1, dress2),   # 穿 女装
)
replies['dress'] = ('本群禁女装', '给你两分钟准备好你的女装')
silence['dress'] = ('禁', '不', '拒绝', '别')


admire1 = ('膜', '摸', '%', 'mo')
admire2 = ('群主', '管理员', '你', '大佬', 'dalao')
chains['admire'] = (
    (admire1, admire2),   # 膜 大佬
)
replies['admire'] = ('本群禁膜', '给你两分钟冷静冷静')
silence['admire'] = ('禁', '不', '拒绝', '别')


c_noun1 = ('c', 'c语言', '编程')
c_noun2 = ('黑客', '信息安全', '安全', '信安')
c_noun3 = ('书', '教材', '资料', '方法')
c_noun4 = ('我', '当', '做', '成为', '搞')
c_adv1 = ('怎么', '如何', '怎样', '咋')
c_verb1 = ('看', '读', '用', '推荐')
c_verb2 = ('想', '教', '要')
c_verb3 = ('入门', '学', '开始')
chains['c'] = (
    ((c_noun1, c_noun2), c_adv1, c_verb3),   # c 怎么 学
    (c_adv1, c_verb3, (c_noun1, c_noun2)),   # 怎么 学 c
    ((c_noun1, c_noun2), c_noun3),           # c 书
    (c_verb2, c_verb3, c_noun1),             # 想 学 c
    (c_noun4, c_noun2),                      # 当 黑客 / 搞 信安
)
replies['c'] = (
    '入门还是要以 C 语言为基础，书籍推荐《C Primer Plus》，最好不要看谭浩强、XX 天精通或者从入门到精通系列…另外，想学 ctf 的话推荐一个网站\nhttps://ctf-wiki.github.io/ctf-wiki/',
    '先把 C 语言学好，其他的不着急，推荐使用《C Primer Plus》，想学 ctf 的话推荐一个网站\nhttps://ctf-wiki.github.io/ctf-wiki/',
)
silence['c'] = ('不', '拒绝', '别')


where_noun1 = ('协会', '安协', '实验室', 'vidar')
where_adv1 = ('哪', '位置', '怎么走', '地址', '地点', '怎么去', '咋去')
chains['where'] = (
    (where_noun1, where_adv1),  # 协会 哪
    (where_adv1, where_noun1),  # 咋去 协会
)
replies['where'] = (
    '协会的两处地方都在一教，一处是南 111，一处是北 300b，基本都有人在，欢迎来自习(听我们吹比)~',
    '协会的地址有一教北 300b 和一教南 111，如果不是太早或太晚基本都有人在，进去后找个地方坐下来学习就行',
)


def _inner_check(item, msg):
    for i in item:
        if i in msg:
            return True
    return False


def check_if_exist(key, msg):
    msg = msg.lower()
    for i in silence.get(key, []):
        if i in msg:
            return False

    for chain in chains[key]:
        for item in chain:
            if isinstance(item[0], tuple) or isinstance(item[0], list):
                for i in item:
                    if _inner_check(i, msg):
                        break
                        # 如果是个列表，里边的关键词都是对等的
                        # 一旦找到一个就 break 跳出来
                        # 继续找下一个 item
                else:
                    break
                    # 如果 item 里所有关键词都没找到，直接跳出来，处理下一条链
            else:
                if not _inner_check(item, msg):
                    break
                    # 如果 item 没找到，直接跳出来，处理下一条链
        else:
            return True
            # 如果完整走到头了，说明这条链完整存在，返回 True
    return False
    # 如果没有任何一条链能完整走到头，那么返回 False


def if_any_autoreply(msg):
    for key in replies.keys():
        if check_if_exist(key, msg):
            return random.choice(replies[key])
    return None
