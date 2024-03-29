#!/usr/bin/python
# encoding=utf-8
from pprint import pprint
import sys
from PIL import Image
from StringIO import StringIO
import time
import shutil
from pytesser import *
import requests
import subprocess
sender = 'no_reply@ok130.com'
RECIVER = '445@qq.com'
ACCOUNT = 'aa'
PASSWORD = 'aa'
INDEX_URL = 'http://www.37cs.com/index.php'
LOGIN_URL = 'http://www.37cs.com/index.php?action=Login&do=login'
QUERY_URL = 'http://www.37cs.com/index.php?action=User&do=manage&method=cpsincome&ajax=data'
LOGIN_STATUS_URL = 'http://www.37cs.com/index.php?action=Login&do=loginStatus'
# requests.get('http://www.37cs.com/index.php?action=Login&do=loginStatus', cookies = cookies)
def cl(image):
    image = image.convert('L')
    image = image.point(lambda x: 0 if x<158 else 255, '1')
    return image

def read(image):
    text = image_to_string(image)
    return text

def get_code():
    global vcode
    global cookies
    timestamp = str(time.time()).split('.')[0] + '000'
    vcode_data = {'action': 'Login','do': 'vcode','t': timestamp}
    r_vcode = requests.get(INDEX_URL,params = vcode_data)
    i = Image.open(StringIO(r_vcode.content))
    i.save('/home/jp2014/png/aa.png')
    gray = cl(i)
    gray.save('/home/jp2014/png/aa_de.png')
    vcode = read(gray)[0:4]
    cookies = r_vcode.cookies
    #print(tuple(r_vcode.cookies))
    #print 'vcode: %s' %vcode
    #print image_file_to_string('/home/jp2014/png/aa.png')

def login():
    login_data = {'user_name': ACCOUNT, 'user_pwd': PASSWORD, 'user_vcode':vcode}
    post_login = requests.post(LOGIN_URL, cookies=cookies,data=login_data)
    ret=post_login.json()
    print ret
    l = ['fail','success']
    print "Login :%s" %l[ret['status']]
    time.sleep(3)
    return ret['status']

def to_table(data):
    head = '''
    <table cellspacing="1" cellpadding="0" border="1" class="tablesorter" style="width:680px" id="my_data"> <thead> <tr> <th>日期</th> <th>游戏平台</th> <th>游戏名称</th> <th>游戏服</th> <th>人数</th> <th>金额</th> </tr> </thead> <tbody> 
    '''
    body=''
    count = len(data)
    consumers=0
    money=0
    for i in range(count):
        BILL_DAY = data[i]['BILL_DAY'].encode('utf-8')
        PLATFORM_NAME =data[i]['PLATFORM_NAME'].encode('utf-8')
        GAME_NAME = data[i]['GAME_NAME'].encode('utf-8')
        SERVER_NAME = data[i]['SERVER_NAME'].encode('utf-8')
        CONSUMERS = data[i]['CONSUMERS'].encode('utf-8')
        CONSUMPTION = data[i]['CONSUMPTION'].encode('utf-8')
        body+="<tr><td><span times=\"\" t=\"5\" style=\"border-bottom:1px dashed #ccc;\">%s</span></td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> </tr><tr></tr>" %(BILL_DAY,PLATFORM_NAME,GAME_NAME,SERVER_NAME,CONSUMERS,CONSUMPTION)
        consumers += int(data[i]['CONSUMERS'])
        money += float(data[i]['CONSUMPTION'])
    body += "</tbody> <tfoot> <tr> <th align=\"center\" colspan=\"1\">总计</th> <th colspan=\"3\">&nbsp;</th> <th>%s</th> <th>%s</th> </tr> </tfoot> </table>" %(consumers, money)
    table = head + body
    return table

def query(start_day):
    try:
        headers = {'Referer':'http://www.37cs.com/user.html',
                'User-Agent':'(Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0',
                'X-Requested-With':'XMLHttpRequest',
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
                }
        end_day=time.strftime('%Y-%m-%d',time.localtime())  
        query_data = {'start_date' : start_day,'end_date' : end_day,'platid' : 0,'gameid':' '}
        last_query_day = end_day
        ret_query = requests.post(QUERY_URL,headers=headers, cookies=cookies,data=query_data)
        if not ret_query.content :
            return false
        else:
            ret = ret_query.json()
            if ret['status']==0:
                return ret['message'].encode('utf-8')
            else:
                table = to_table(ret['data'])
                return  (table,last_query_day)
    except:
        return '程序查询数据错误'
def mail_notify(sender, RECIVER, content):
    html_wrap = '''
    <html>
    <head></head>
    <body>
    xxx
    </body>
    </html>
        '''
    import smtplib
    import time
    from email.MIMEMultipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart()
    msg['Subject'] = '充值统计-1: %s' % time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
    msg['From'] = sender
    msg['To'] = RECIVER
    try:
        mail_content = html_wrap.replace('xxx', content.replace('border="0"', 'border="1"'))
    except:
        mail_content = content
    msg.attach(MIMEText(mail_content, 'html'))
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, RECIVER.split(), msg.as_string())
    s.quit()

def running():
    cmdline='ps aux |egrep "/usr/bin/python.*query_cps.py"|grep -v grep |wc -l'
    ret=subprocess.Popen(cmdline,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, errors = ret.communicate()
    output = int(output)
    if output == 1:
        return True
    else:
        return False

if __name__ == '__main__':
    start_day=time.strftime('%Y-%m-%d',time.localtime())
    if not running():
        sys.exit()
    login_code = 0
    count=0
    fail=0
    while(login_code == 0):
        get_code()
        time.sleep(3)
        login_code = login()
    while True:
        if(count==0 or (count%30)==0):
            content, start_day = query(start_day)
            if(content):
                mail_notify(sender, RECIVER, content)
            else:
                fail+=1
        if(fail>3):
            break
        time.sleep(120)
        requests.get(LOGIN_STATUS_URL,cookies=cookies)
        count+=1
