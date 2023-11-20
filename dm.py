import json
import logging
import sys
import time

import requests


class LogColor:
    # logging日志格式设置
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(message)s')

    @staticmethod
    def info(message: str):
        # info级别的日志，绿色
        logging.info("\033[0;32m" + message + "\033[0m")

    @staticmethod
    def warning(message: str):
        # warning级别的日志，黄色
        logging.warning("\033[0;33m" + message + "\033[0m")

    @staticmethod
    def error(message: str):
        # error级别的日志，红色
        logging.error("\033[0;31m" + "-" * 120 + '\n| ' + message + "\033[0m" + "\n" + "└" + "-" * 150)

    @staticmethod
    def debug(message: str):
        # debug级别的日志，灰色
        logging.debug("\033[0;37m" + message + "\033[0m")


class Student:
    def __init__(self, phone, pwd):
        self.info = None
        self.s = requests.Session()
        self.phone = phone
        self.pwd = pwd
        self.domain = 'https://appdmkj.5idream.net/v2/'
        self.version = '4.6.0'
        self.h = {"channelName": "dmkj_Android", "countryCode": "CN", "createTime": int(1000 * time.time()),
                  "device": "Redmi 23013RK75C", "hardware": "qcom", "modifyTime": int(1000 * time.time()),
                  "jPushId": "18071adc020b819c5c9",
                  "operator": "%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A", "screenResolution": "1080-2116",
                  "startTime": int(1000 * time.time()),
                  "sysVersion": "Android 29 10", "system": "android",
                  "uuid": "A4:60:46:1F:74:BF", "version": self.version}

    def getSign(self, data, timestamp=None):
        if timestamp is None:
            data['timestamp'] = str(int(1000 * time.time()))
        else:
            data['timestamp'] = str(int(timestamp))
        signData = requests.post('http://kp81n2es.shenzhuo.vip:41756/api/sign',
                                 json={'token': 'xxx', 'data': json.dumps(data), }).json()
        if signData['code'] == 200:
            LogColor.info(f"数据签名成功：{data} {signData['d']}")
            return signData['d']
        LogColor.error(signData['msg'])

    def req(self, url, d):
        return self.s.post(f'{self.domain}{url}', headers={
            'standardUA': json.dumps(self.h),
            'User-Agent': 'okhttp/3.11.0',
            'Host': 'appdmkj.5idream.net'
        }, data={
            'd': d
        }).json()

    def login(self):
        data = {"account": self.phone, "pwd": self.pwd,
                "timestamp": int(1000 * time.time()), "version": self.version}
        login = self.req('login/phone', self.getSign(data))
        if login['code'] == '100':
            self.info = login['data']
        else:
            if login.get("msg"):
                return login.get("msg")
            return login['actionSheet']['content']

    def activities(self):
        data = {
            'joinStartTime': '',
            'token': self.info['token'],  # 登陆接口获取
            'startTime': '',
            'endTime': '',
            'joinFlag': '',
            'collegeFlag': '',
            'catalogId': '',
            'joinEndTime': '',
            'specialFlag': '',
            'status': '',
            'keyword': '',
            'version': self.version,
            'uid': self.info['uid'],  # 登陆接口获取
            'sort': '',
            'page': '1',
            'catalogId2': '',
            'level': '',
        }
        return self.req('activity/activities', self.getSign(data))

    def getDetail(self, aid):
        data = {
            'uid': self.info['uid'],
            'token': self.info['token'],
            'activityId': aid,
            'version': self.version
        }
        return self.req('activity/detail', self.getSign(data))

    def submit(self, aid, get_data=False):
        info = [{"conent": "", "content": "", "fullid": "79857", "key": 1, "notList": "false", "notNull": "false",
                 "system": 0,
                 "title": "姓名"}]
        data = {
            'uid': self.info['uid'],  # 登陆接口获取
            'token': self.info['token'],  # 登陆接口获取
            'data': json.dumps(info),  # 活动报名参数
            'remark': '',
            'activityId': aid,  # 活动ID
            'version': self.version
        }
        if get_data:
            return data
        return self.req('signup/submit', self.getSign(data))

    def select(self):
        activities = self.activities()['data']['list']
        ind = 1
        for a in activities:
            # 过滤状态
            if a["statusText"] not in ['已结束']:
                LogColor.info(f'{ind}.{a["name"]} --- {a["activitytime"]} {a["statusText"]} ')
            ind += 1
        s = int(input("请选择活动："))
        activityId = activities[s - 1]['activityId']
        detail = self.getDetail(activityId)['data']
        LogColor.info(f'活动名称：{detail["activityName"]} 报名时间：{detail["joindate"]}')
        stime = detail["joindate"].split("-")[0]
        LogColor.info(f'提交成功，程序将于：{stime}自动报名')
        timeArray = time.strptime(stime, "%Y.%m.%d %H:%M")
        timeStamp = int(time.mktime(timeArray))
        # 报名已开始，当前时间为时间戳
        sub_time = time.time() * 1000
        # 未开始报名，将报名时间为时间戳，防止签名过期
        if timeStamp > sub_time:
            sub_time = timeStamp * 1000
        # 提取将数据签名，避免循环请求签名，时间戳为报名开始时间
        submitData = self.getSign(self.submit(activityId, True), sub_time)
        while True:
            t = time.time()
            se = timeStamp - t
            LogColor.info(f"距离活动报名开始还剩：{se}秒")
            if se > 60:
                time.sleep(30)
            elif se > 3:
                time.sleep(1)
            elif -3 <= se <= 3:
                submit = self.req('signup/submit', submitData)
                LogColor.info(str(submit))
                if submit['code'] == '100':
                    LogColor.error("提交成功，任务停止！")
                    break
            else:
                submit = self.req('signup/submit', submitData)
                LogColor.info(str(submit))
                LogColor.error("提交成功，任务停止！")
                break


if __name__ == '__main__':
    # 输入类型1，代码写死
    account = ''
    password = ''
    # 输入类型2，命令传参
    if len(sys.argv) == 3:
        account = sys.argv[1]
        password = sys.argv[2]
    # 输入类型3，控制台输入
    if not account or not password:
        account = input("请输入账号：")
        password = input("请输入密码：")
    student = Student(account, password)
    login = student.login()
    if login:
        LogColor.warning(login)
    else:
        LogColor.info(f"登录成功：{student.info['name']}({student.info['nickname']}) --- {student.info['schoolName']}")
        while True:
            student.select()
            s = input("是否继续：")
            if s == '否':
                break
    time.sleep(100)
