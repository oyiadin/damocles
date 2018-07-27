import sqlite3
import random
from globals import *
import re
from base import whitelist

conn = sqlite3.connect("sqli.db", check_same_thread=False)


# 初始化数据库
def init():
    flag = "flag{Good_job!u_will_get_bonus!}"
    conn.execute("CREATE TABLE IF NOT EXISTS `USER`(USER_ID VARCHAR(11) UNIQUE ,NUMBER INT NOT NULL DEFAULT 0) ")
    conn.execute("CREATE TABLE IF NOT EXISTS `CODES`(CODE VARCHAR(10))")
    conn.execute("CREATE TABLE IF NOT EXISTS `flaG`(flaG VARCHAR(50) UNIQUE )")
    for i in whitelist:
        try:
            conn.execute("INSERT INTO `USER`(`USER_ID`) VALUES(%s)" % (i))
        except sqlite3.IntegrityError:
            continue
    try:
        conn.execute("INSERT INTO `flaG`(`flaG`) VALUES('%s')" % (flag))
    except sqlite3.IntegrityError:
        pass
    conn.commit()


def waf(string):
    string = str(string).upper().replace('DROP', '')  # 单纯的防止频繁删除数据表
    # return re.sub('OR|UNION|SELECT', '', string, 1)
    return string


# 生成激活码
def createActivationCode(amount):
    amount_now = conn.execute("SELECT COUNT(`CODE`) FROM `CODES`").fetchone()[0]
    if amount <= 20 and amount + amount_now <= 100:
        nums = [str(i) for i in range(10)]
        for i in range(int(amount)):
            ActivationCode = ''
            for n in range(9):
                ActivationCode += random.choice(nums)
            conn.execute("INSERT INTO `CODES`(`CODE`) VALUES(%s)" % (ActivationCode))
        conn.commit()
        return dict(reply=prompts['bonus_create_code_succeed'] % (amount, amount + amount_now))
    else:
        return dict(reply=prompts['bonus_create_code_failed'])


# 输出所有激活码
def getActivationCode():
    ActivationCodesList = [i[0] for i in conn.execute("SELECT * FROM `CODES`").fetchall()]
    return dict(reply=' '.join(ActivationCodesList))


# 领取Bonus
def getBonus(qq, ActivationCode):
    ActivationCode = waf(ActivationCode)
    try:
        result = conn.execute(
            "SELECT * FROM `CODES` WHERE (%s IN (SELECT `USER_ID` FROM USER)) AND `CODE`=%s" % (qq, ActivationCode))
        if result.fetchone() is not None:
            conn.execute(
                "UPDATE `USER` SET `NUMBER`=(SELECT `NUMBER` FROM `USER` WHERE `USER_ID`=%s) + 1 WHERE `USER_ID`=%s" % (
                    qq, qq))
            conn.execute("DELETE FROM `CODES` WHERE `CODE`=%s" % (ActivationCode))
            conn.commit()
            number = conn.execute("SELECT `NUMBER` FROM `USER` WHERE `USER_ID`=%s" % (qq)).fetchone()
            return dict(reply=prompts['bonus_get_bonus_succeed'] % (number))
        else:
            return dict(reply=prompts['bonus_get_bonus_failed'])
    except TypeError:
        return dict(reply=prompts['bonus_get_bonus_failed'])
    except (sqlite3.OperationalError, sqlite3.Warning) as message:
        return dict(reply=prompts['bonus_sqlite_error'] % message)
