import sqlite3
import random
from globals import *
import re
from base import whitelist
conn = sqlite3.connect("sqli.db")


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
    return re.sub('OR|UNION|SELECT', '', string, 1)


def createActivationCode(numbers):
    nums = [str(i) for i in range(10)]
    for i in range(int(numbers)):
        ActivationCode = ''
        for n in range(9):
            ActivationCode += random.choice(nums)
        conn.execute("INSERT INTO `CODES`(`CODE`) VALUES(%s)" % (ActivationCode))
    conn.commit()
    return True


def getActivationCode():
    ActivationCodesList = [i[0] for i in  conn.execute("SELECT * FROM `CODES`").fetchall()]
    return dict(reply=ActivationCodesList)


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
            return dict(reply='恭喜你成功领取一个星球杯! 你当前共有星球杯%s个' % (number))
        else:
            return dict(reply='错误的激活码或你没有权限领取')
    except TypeError:
        return dict(reply='错误的激活码或你没有权限领取')
    except sqlite3.OperationalError as message:
        return dict(reply='%s' % message)


