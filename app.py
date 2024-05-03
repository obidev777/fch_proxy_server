from flask import Flask,jsonify,request
try:
    import requests as rq
    from requests.structures import CaseInsensitiveDict
    rq.packages.urllib3.disable_warnings()
except:pass
import time
import threading
from MoodleClient import MoodleClient as MC 
from NexCloudClient import NexCloudClient as NC 
import S5Crypto as s5 
import os
import json

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
def createID(count=8):
    from random import randrange
    map = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id = ''
    i = 0
    while i<count:
        rnd = randrange(len(map))
        id+=map[rnd]
        i+=1
    return id

app = Flask(__name__)

REQUESTS = {}

def handle_responsee(**data):
    global REQUESTS
    id = data['id']
    url = data['url']
    headers = None
    stream = False
    if 'stream' in data:
        stream = data['stream']
    host = 'https://eva.uo.edu.cu/'
    if 'host' in data:
        host = data['host']
    username = s5.decrypt('R&e-M$S;V_Q,c-._M;J;E$=,K,=%')
    if 'username' in data:
        username = data['username']
    password = s5.decrypt('B&M:J-E%=$K:=_+&,&,$')
    if 'password' in data:
        password = data['password']
    repoid = 4
    if 'repoid' in data:
        repoid = data['repoid']
    if 'headers' in data:
        headers = data['headers']
    cookies = None
    if 'cookies' in data:
        headers = data['cookies']
    chunk_split = 99
    chunk_min_split = 1
    chunk_content = 2
    close_time = 10
    if chunk_split in data:
        chunk_split = int(data['chunk_split'])
    if id not in REQUESTS:
        REQUESTS[id] = {'id':id,'headers':{},'cookies':{},'content':[],'timespan':time.time(),'complete':False}
    sess = rq.Session()
    if cookies:
        sess.cookies.update(cookies)
    close_request = False
    resp = sess.get(url,headers=headers,stream=True)
    REQUESTS[id]['timespan'] = time.time()
    if(resp.status_code==200):
        REQUESTS[id]['cookies'] = sess.cookies.get_dict()
        contentlen = 1
        try:
            contentlen = len(resp.text)
        except:
            try:
                contentlen = int(resp.headers['Content-Length'])
            except:pass
        REQUESTS[id]['time_close'] = close_time
        REQUESTS[id]['headers'] = resp.headers
        REQUESTS[id]['headers']['Content-Length'] = str(contentlen)
        cli = MC(username,password,host,repoid)
        loged = cli.login()
        if not stream:
            data = b''
            bytesread = 0
            t = time.time()
            for chunk in resp.iter_content(1024):
                if time.time() - t >= 1:
                    print(sizeof_fmt(bytesread))
                    t = time.time()
                if (time.time()-REQUESTS[id]['timespan'])>=close_time or not loged:
                    close_request = True
                data+=chunk
                bytesread+=len(chunk)
                if close_request: 
                    data = b''
                    break
                if bytesread>=contentlen or len(REQUESTS[id]['content'])<chunk_content and len(data)>(1024*1024*chunk_min_split) or len(data)>=(1024*1024*chunk_split):
                    tmpn = 'temp'+createID()+'.pdf'
                    temp = open(tmpn,'wb')
                    temp.write(data)
                    temp.close()
                    uploaded = None
                    while loged:
                        if uploaded:break
                        try:
                            uploaded = cli.upload_file_draft(tmpn)[1]['url']
                        except Exception as ex:
                            print(f'Upload File Draft : {str(ex)}')
                            try:
                                uploaded = cli.upload_file_perfil(tmpn)[1]['url']
                            except Exception as ex:
                                print(f'Upload File Perfil : {str(ex)}')
                                try:
                                    uploaded = cli.upload_file_calendar(tmpn)[1]['url']
                                except Exception as ex:
                                    try:
                                        if TOKEN_MOODLE:
                                            uploaded = cli.upload_with_token(tmpn)
                                    except:
                                        print(f'Upload File Calendar : {str(ex)} Moodle Not Upload System!')
                                        uploaded = None
                    if uploaded:
                        REQUESTS[id]['cookies'] = cli.get_cookies()
                        REQUESTS[id]['content'].append(uploaded)
                        data = b''
                        try:
                            os.unlink(tmpn)
                        except:pass
    else:
        REQUESTS.pop(id)
    if close_request:
        REQUESTS.pop(id)
    else:
        REQUESTS[id]['complete'] = True


@app.route('/POST/<id>',methods=['POST'])
def POST(id=None):
    global REQUESTS
    data = None
    try:
        if not data:
            data = request.json
    except:pass
    try:
        if not data:
            data = request.form
    except:pass
    if id in REQUESTS:
        if data:
            for item in data:
                if item in REQUESTS:
                    REQUESTS[item] = data[item]
            return REQUESTS[id],200
    return 'BAD',405

@app.route('/GET',methods=['GET','POST'])
def GET():
    data = None
    try:
        if not data:
            data = request.json
    except:pass
    try:
        if not data:
            data = request.form
    except:pass
    if data:
        data['id'] = createID()
        threading.Thread(target=handle_responsee,kwargs=data).start()
        return data['id'],200
    return 'BAD',405

@app.route('/status/<id>',methods=['GET'])
def Status(id):
    global REQUESTS
    if id in REQUESTS:
        REQUESTS[id]['timespan'] = time.time()
        data = str(REQUESTS[id])
        return data,200
    else:
        return 'NO id In Data',405

@app.route('/remove/content/<id>',methods=['GET','POST'])
def RemoveContent(id):
    global REQUESTS
    data = None
    try:
        if not data:
            data = request.json
    except:pass
    try:
        if not data:
            data = request.form
    except:pass
    if id in REQUESTS:
        for item in REQUESTS[id]['content']:
            if data['url'] in item:
                REQUESTS[id]['content'].remove(data['url'])
                break
        return 'OK',200
    else:
        return 'NO id In Data',405

if __name__ == '__main__':
    app.run('0.0.0.0',port=6590)