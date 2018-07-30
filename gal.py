from time import sleep
import random
import json
from base import *
'''
scenario_list[天数][情景][故事和选项]  {选项:[结果,第二天可能出现的情景]}
以上需要一个生成器来生成
savedata = {'qq号':[level,可能出现的情景]}
'''

'''
scenario_list =
[
	[#Day1
		('有一天，我和她相遇了',{'亲上去':['被打死',[-1]],'转身离开':['你错过人生中最重要的相遇...',[2]]}),
		('薯片姐姐想和你打ctf',{'399一次':['那一夜发生的事情你不愿再提',[0,1]],'转身离开':['薯片姐姐你都不理，乙烷',[-1]]}),
	],
	[#Day2	
		('o爷爷想和你打ctf',{'o爷爷！o爷爷！':['o爷爷还没有学习好，并没有成功带飞你',[1,2]],'转身离开':['o爷爷你都不理，乙烷',[-1]]}),
		('Aris想和你打ctf',{'辣鸡Aris，滚开':['你做出了明智的选择',[2]],'好啊！':['Aris把你坑死了！',[-1]]}),
		('第二天，我又碰到了她',{'抱上去':['又被打死，我为什么说又呢...',[-1]],'转身离开':['嗯，很好，实力单身',[-1]]}),
	],
	[#Day3	
		('o爷爷想和你打ctf',{'o爷爷！o爷爷！':['o爷爷把你带飞了',[]],'转身离开':['o爷爷你都不理，乙烷',[1]]}),
		('Aris想和你打ctf',{'辣鸡Aris，滚开':['你没有时间拯救自己了，重来吧',[-1]],'好啊！':['Aris把你坑死了！',[-1]]}),
		('Aris还想和你打ctf',{'辣鸡Aris，死开啊':['。。。。',[-1]],'原谅我，Aris！':['Aris是菜，但所谓不要得罪作者的真理你终于懂了',[]]}),
	],
]
'''
scenario_list = []

def scn_init():
	global scenario_list
	global best_player
	fp = open('火车游戏.txt','r',encoding='utf-8')
	s = fp.read()
	start = re.search(R'\[Day\d+\]',s).start()
	end = re.search(R'\[final\]',s).start()-1
	s = s[start:end]
	now = re.search(R'\[Day\d+\]',s)
	while now != None:
		#获得时间
		day = int(re.search(R'\d+',s[now.start():now.end()-1]).group())
		if len(scenario_list) < day:
			for i in range(day-len(scenario_list)):
				scenario_list.append([])
		s = s[now.end():]
		#获得编号
		now = re.search(R'\[\d+\]',s)
		num = int(re.search(R'\d+',s[now.start():now.end()-1]).group())
		s = s[re.search(R'\[\d+\]\n*',s).end():]
		#获得情景
		now = re.search(R'\[end\]\n*',s)
		story = s[:now.start()-1]
		s = s[now.end():]
		part = {}
		now = re.search(R'\[>-?\d*[,\d*]*\]',s)
		nextD = re.search(R'\[Day\d+\]',s)
		if nextD != None:
			today = s[:nextD.start()]
			s = s[nextD.start():]
		else:
			today = s
		while now != None:
			#获取选择项
			choice = today[0:now.start()]
			end = re.search(R'\n*\[end\]\n*',today).start()
			#获取后续情景
			atfer = today[now.end():end]
			#获取后续下一天故事
			nextnum = re.split(R',',today[now.start()+2:now.end()-1])
			nextnum = [int(i) for i in nextnum if i != '']
			part[choice] = [atfer,nextnum]
			today = today[re.search(R'\n*\[end\]\n*',today).end():]
			now = re.search(R'\[>-?\d*[,\d*]*\]',today)
		scenario_list[day-1].append((story,part))
		now = re.search(R'\[Day\d+\]',s)
	best_player = [0,[0]]
savedata = {}

play_on = {}

best_player = []

def startgame(cxt):
	global scenario_list
	global savedata
	global play_on
	global best_player
	help_message = 'galbot_v0.1——\n'
	help_message+= '欢迎进入大型多人在线Galgame，通称MMOGAL\n'
	help_message+= '使用%gal命令可以开始游戏，进入下一关也请使用这条命令\n'
	help_message+= '每个人的游戏进度单独记录，请直接输入选项中的文字进行回答\n'
	help_message+= '现版本只实装了火车游戏(前半段)，请互相配合合理利用信息过关\n'
	help_message+= '您可以使用%gal help再次查看这条帮助'
	if len(cxt['message']) == 9:#%gal help
		if cxt['message'][5:] == 'help':
			bot.send(cxt,
			message=help_message,
			at_sender=True)
			return
	if len(cxt['message']) == 12:#%gal deldata
		if cxt['message'][5:] == 'deldata':
			bot.send(cxt,
			message='游戏存档已删除',
			at_sender=True)
			savedata = {}
			best_player = [0,[0]]
			with open("./gal.json",'w',encoding='utf-8') as json_file:
				json.dump(savedata,json_file,ensure_ascii=False)
			return
	#加载存档
	try:
		with open("./gal.json",'r',encoding='utf-8') as json_file:
			savedata=json.load(json_file)
	except FileNotFoundError:
		pass
	player = str(cxt['user_id'])
	if '0' in savedata:
		best_player = savedata['0']
	if player in play_on:
		if(play_on[player] == -1):
			return
	#如果没有该玩家的存档则创建一个
	if not player in savedata:
		if len(savedata) <= 4:
			level = 0
			count = len(scenario_list[level])
			nextL = [i for i in range(0,count)]
			savedata[player] = [level,nextL]
		else:
			bot.send(cxt,
			message='当前游戏人数已达上限，请等待游戏结束',
			at_sender=True)
	else:
		level = savedata[player][0]
		nextL = savedata[player][1]
		count = len(nextL)
	#随机读取下一个场景
	rdnum = random.randint(0,count-1)
	rdnum = nextL[rdnum]
	#发送情景
	text = re.split(R'\[next\]\n*',scenario_list[level][rdnum][0])
	bot.send(cxt,
	message='Day' + str(level + 1),
	at_sender=True)
	sleep(1)
	for i in text:
		if i != '':
			bot.send(cxt,
			message=i,
			at_sender=True)
			takesleep(len(i))
	#发送选项
	select = scenario_list[level][rdnum][1]
	i = 1
	sel_str = ''
	for key in select:
		sel_str += str(i) + '.' + key + '\n'
		i = i + 1
	bot.send(cxt,
	message=sel_str[:-1],
	at_sender=True)
	play_on[player] = rdnum


def makechoice(cxt):
	global savedata
	global play_on
	global best_player
	player = str(cxt['user_id'])
	#判断玩家是否正在玩gal，不是则直接返回
	if not player in play_on or not player in savedata:
		return
	if play_on[player] == -1:
		return
	level = savedata[player][0]
	rdnum = play_on[player]
	nextL = savedata[player][1]
	s = cxt['message']
	#判断玩家输入的是否为gal选项，不是则返回
	isgal = False
	for choices in scenario_list[level][rdnum][1]:
		ans = re.search(R'「.+」',choices)
		if ans != None:
			ans = choices[ans.start()+1:ans.end()-1]
		else:
			ans = choices
		if s == ans or s == choices:
			text = re.split(R'\[next\]\n*',scenario_list[level][rdnum][1][choices][0])
			isgal = True
			for i in text:
				if i != '':
					bot.send(cxt,
					message=i,
					at_sender=True)
					takesleep(len(i))
			#玩家已做出选择，更新游戏存档
			savedata[player] = [level + 1,scenario_list[level][rdnum][1][choices][1]]
			nextL = savedata[player][1]
			if savedata[player][0] > best_player[0] and nextL != [-1] and nextL != []:
				best_player = savedata[player]
				savedata['0'] = best_player
				bot.send(cxt,
				message='最佳玩家记录已刷新，bad end之后的玩家将更新记录到此处',
				at_sender=True)
			break
	if not isgal:
		return
	#'第二天可能出现的情景'出现[]为good end，[-1]是定死的bad end，最后一天的非[]代表暂为bad end，可能因为天数的增加转为good end
	if nextL == [-1] or level == len(scenario_list) and nextL != []:
		bot.send(cxt,
		message='bad end!',
		at_sender=True)
		savedata[player] = best_player
		bot.send(cxt,
		message='已将您的进度恢复到最佳玩家的记录状态，具体为Day' + str(best_player[0] + 1) + '，您可以继续游戏！',
		at_sender=True)
	elif nextL == []:
		bot.send(cxt,
		message='good end!',
		at_sender=True)
		bot.send(cxt,
		message='全员通关恭喜！游戏存档已清空，已经可以开始下一轮游戏',
		at_sender=True)
		savedata = {}
	del play_on[player]#设置成=-1时每人只能玩一次
	#保存数据
	with open("./gal.json",'w',encoding='utf-8') as json_file:
		json.dump(savedata,json_file,ensure_ascii=False)


def takesleep(leng):
	sleep(1 + leng/15)
