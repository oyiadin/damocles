import re
import time
import json
import random

from base import *
from globals import *


scenario_list = []
savedata = {}
play_on = {}
best_player = []
playing = False


def sleep(leng):
    time.sleep(1 + leng / 15)


def scn_init():
    global scenario_list
    global best_player
    best_player = [0, [0]]

    text = open('火车游戏.txt', 'r', encoding='utf-8').read()
    start = re.search(R'\[Day\d+\]', text).start()
    end = re.search(R'\[final\]', text).start() - 1
    text = text[start:end]
    now = re.search(R'\[Day\d+\]', text)

    while now != None:
        # 获得时间
        day = int(re.search(R'\d+', text[now.start():now.end() - 1]).group())
        if len(scenario_list) < day:
            for i in range(day - len(scenario_list)):
                scenario_list.append([])
        text = text[now.end():]

        # 获得编号
        now = re.search(R'\[\d+\]', text)
        num = int(re.search(R'\d+', text[now.start():now.end() - 1]).group())
        text = text[re.search(R'\[\d+\]\n*', text).end():]

        # 获得情景
        now = re.search(R'\[end\]\n*', text)
        story = text[:now.start() - 1]
        text = text[now.end():]
        part = {}
        now = re.search(R'\[>-?\d*[,\d*]*\]', text)
        nextD = re.search(R'\[Day\d+\]', text)
        if nextD != None:
            today = text[:nextD.start()]
            text = text[nextD.start():]
        else:
            today = text

        while now != None:
            # 获取选择项
            choice = today[0:now.start()]
            end = re.search(R'\n*\[end\]\n*', today).start()
            # 获取后续情景
            after = today[now.end():end]
            # 获取后续下一天故事
            next_num = re.split(R',', today[now.start() + 2:now.end() - 1])
            next_num = [int(i) for i in next_num if i != '']
            part[choice] = [after, next_num]
            today = today[re.search(R'\n*\[end\]\n*', today).end():]
            now = re.search(R'\[>-?\d*[,\d*]*\]', today)

        scenario_list[day - 1].append((story, part))
        now = re.search(R'\[Day\d+\]', text)


def startgame(cxt):
    global scenario_list
    global savedata
    global play_on
    global best_player
    global playing

    if playing == True:
        return
    else:
        playing = True

    if len(cxt['groups']) == 2:
        if cxt['groups'][1] == 'help':
            playing = False
            return dict(reply=prompts['gal_help'])

        if cxt['groups'][1] == 'deldata':
            if cxt['user_id'] in whitelist:
                bot.send(cxt, message=prompts['gal_deleted'])
                savedata = {}
                play_on = {}
                best_player = [0, [0]]
                with open("./gal.json", 'w', encoding='utf-8') as json_file:
                    json.dump(savedata, json_file, ensure_ascii=False)
            else:
                bot.send(cxt,message=prompts['permission_needed'])
            playing = False
            return

    # 加载存档
    try:
        with open("./gal.json", 'r', encoding='utf-8') as json_file:
            savedata = json.load(json_file)
    except FileNotFoundError:
        pass
    player = str(cxt['user_id'])
    if '0' in savedata:
        best_player = savedata['0']
    if player in play_on:
        if play_on[player] == -1:
            playing = False
            return

    # 如果没有该玩家的存档则创建一个
    if not player in savedata:
        if len(savedata) <= 5:
            level = 0
            count = len(scenario_list[level])
            nextL = [i for i in range(0, count)]
            savedata[player] = [level, nextL]
        else:
            bot.send(cxt, message=prompts['gal_too_many_players'])
            playing = False
            return
    else:
        level = savedata[player][0]
        nextL = savedata[player][1]
        count = len(nextL)

    # 随机读取下一个场景
    rdnum = random.randint(0, count - 1)
    rdnum = nextL[rdnum]

    # 发送情景
    text = re.split(R'\[next\]\n*', scenario_list[level][rdnum][0])
    bot.send(cxt, message='Day' + str(level + 1))
    sleep(1)

    for i in text:
        if i != '':
            bot.send(cxt, message=i)
            sleep(len(i))

    # 发送选项
    select = scenario_list[level][rdnum][1]
    i = 1
    sel_str = ''
    for key in select:
        sel_str += str(i) + '.' + key + '\n'
        i = i + 1
    bot.send(cxt, message=sel_str[:-1])
    play_on[player] = rdnum
    playing = False


def makechoice(cxt):
    global savedata
    global play_on
    global best_player
    global playing

    if playing == True:
        return
    else:
        playing = True

    player = str(cxt['user_id'])
    # 判断玩家是否正在玩gal，不是则直接返回
    if not player in play_on or not player in savedata:
        playing = False
        return
    if play_on[player] == -1:
        playing = False
        return

    level = savedata[player][0]
    rdnum = play_on[player]
    nextL = savedata[player][1]
    s = cxt['message']

    # 判断玩家输入的是否为gal选项，不是则返回
    isgal = False
    for choices in scenario_list[level][rdnum][1]:
        ans = re.search(R'「.+」', choices)
        if ans != None:
            ans = choices[ans.start() + 1:ans.end() - 1]
        else:
            ans = choices
        if s == ans or s == choices:
            text = re.split(
                R'\[next\]\n*', scenario_list[level][rdnum][1][choices][0])
            isgal = True
            for i in text:
                if i != '':
                    bot.send(cxt, message=i)
                    sleep(len(i))
            # 玩家已做出选择，更新游戏存档
            savedata[player] = [level + 1,
                                scenario_list[level][rdnum][1][choices][1]]
            nextL = savedata[player][1]
            if savedata[player][0] > best_player[0] and nextL != [-1] and nextL != []:
                best_player = savedata[player]
                savedata['0'] = best_player
                bot.send(cxt, message=prompts['gal_new_best'])
            break
    if not isgal:
        playing = False
        return

    # 第二天可能出现的情景
    # 出现[]为good end，[-1] 是定死的bad end，最后一天的非[]代表暂为bad end，可能因为天数的增加转为good end
    if nextL == [-1] or level == len(scenario_list) and nextL != []:
        bot.send(cxt, message='bad end!')
        savedata[player] = best_player
        bot.send(
            cxt, message=prompts['gal_restore_best'].format(best_player[0] + 1))
    elif nextL == []:
        bot.send(cxt, message='good end!')
        bot.send(cxt, message=prompts['gal_all_passed'])
        savedata = {}
    del play_on[player]  # 设置成=-1时每人只能玩一次
    # 保存数据
    with open("./gal.json", 'w', encoding='utf-8') as json_file:
        json.dump(savedata, json_file, ensure_ascii=False)
    playing = False
