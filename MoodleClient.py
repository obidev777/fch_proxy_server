import requests
import os
import textwrap
import re
import json
from random import random
from random import randint
import urllib
from bs4 import BeautifulSoup
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import uuid
import time
from ProxyCloud import ProxyCloud
import socket
import socks
import urllib
import asyncio

import threading
import urllib.parse
import S5Crypto
import draft_to_calendar
import datetime

from io import BufferedReader, FileIO
from pathlib import Path

import requests
import json
from bs4 import BeautifulSoup
from python_socks import ProxyType

import ProxyCloud
import base64
import os
from requests_toolbelt.multipart import encoder

import aiohttp
from aiohttp_socks import ProxyConnector
import time

from pyobigram.readers import FileProgressReader

def get_webservice_token(host='',username='',password='',proxy:ProxyCloud=None):
    try:
        pproxy = None
        if proxy:
            pproxy=proxy.as_dict_proxy()
        webserviceurl = f'{host}login/token.php?service=moodle_mobile_app&username={username}&password={password}'
        resp = requests.get(webserviceurl, proxies=pproxy,timeout=8)
        data = json.loads(resp.text)
        if data['token']!='':
            return data['token']
        return None
    except:
        return None

store = {}
def create_store(name,data):
    global store
    store[name] = data
def get_store(name):
    if name in store:
        return store[name]
    return None
def store_exist(name):return (name in store)
def clear_store():store.clear()

async def webservice_upload_file(host='',token='',filepath='',progressfunc=None,args=None,proxy:ProxyCloud=None):
    try:
        webserviceuploadurl = f'{host}/webservice/upload.php?token={token}&filepath=/'
        filesize = os.stat(filepath).st_size
        of = FileProgressReader(filepath,1024,progressfunc,args)
        files={filepath: of}
        jsondata = '[]'
        if proxy:
            connector = ProxyConnector(
                 proxy_type=ProxyType.SOCKS5,
                 host=proxy.ip,
                 port=proxy.port,
                 rdns=True,
                 ssl=False
            )
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(webserviceuploadurl, data={filepath: of}) as response:
                    jsondata = await response.text()
                await session.close()
        else:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(webserviceuploadurl, data={filepath: of}) as response:
                    jsondata = await response.text()
                await session.close()
        #resp = requests.post(webserviceuploadurl,data={filepath:of}, proxies=pproxy)
        of.close()
        data = json.loads(jsondata)
        print(data)
        if len(data)>0:
            i=0
            print('parsing json data')
            for item in data:
                item['host'] = host
                item['token'] = token
                data[i] = item
                i+=1
            create_store(filepath,[data,None])
            return data
        create_store(filepath,[None,data])
        return None
    except Exception as ex:
        create_store(filepath,[None,ex])
        print(str(ex))
        return None

def make_draft_urls(data):
    result = None
    if data:
        result = []
        for item in data:
            ctxid = item['contextid']
            itemid = item['itemid']
            filename = item['filename']
            result.append(f'{item["host"]}draftfile.php/{ctxid}/user/draft/{itemid}/{filename}')
    return result


def __progress(filename,current,total,spped,time,args=None):
    print(f'Downloading {filename} {current}/{total}')


import asyncio

class CallingUpload:
                def __init__(self, func,filename,args):
                    self.func = func
                    self.args = args
                    self.filename = filename
                    self.time_start = time.time()
                    self.time_total = 0
                    self.speed = 0
                    self.last_read_byte = 0
                def __call__(self,monitor):
                    self.speed += monitor.bytes_read - self.last_read_byte
                    self.last_read_byte = monitor.bytes_read
                    if time.time() - self.time_start>=1:
                            clock_time = (monitor.len - monitor.bytes_read) / (self.speed)
                            if self.func:
                                self.func(this,self.filename,monitor.bytes_read,monitor.len,self.speed,clock_time,self.args)
                            self.time_start = time.time()
                            self.speed = 0
                            

class MoodleClient(object):
    def __init__(self, user,passw,host='',repo_id=4,proxy:ProxyCloud=None):
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.path = 'https://moodle.uclv.edu.cu/'
        self.host_tokenize = 'https://tguploader.url/'
        if host!='':
            self.path = host
        self.userdata = None
        self.userid = ''
        self.repo_id = repo_id
        self.sesskey = ''
        self.proxy = None
        if proxy :
           self.proxy = proxy.as_dict_proxy()
        self.parsedata = None
        self.parsing = False
        self.profiles = []
        self.loged = False
        self.cookies = None
        self.TOKEN = None
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.36Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.36'}

    def getsession(self):
        return self.session

    def set_token(self,token):
        self.TOKEN = token

    def parse_calendar_with_token(self,resp,url):
        url_convert = f"{self.path}/webservice/rest/server.php?moodlewsrestformat=json"
        url_plus = urllib.parse.quote_plus(url)
        payload_convert =  {"formdata":f"name=Evento&eventtype=user&timestart[day]=5&timestart[month]=2&timestart[year]&timestart[year]=5000&timestart[hour]=23&timestart[minute]=55&description[text]={url_plus}&description[format]=1&description[itemid]={randint(100000000,999999999)}&location=&duration={time.time()+(60*60*24)}&repeat=0&id=0&userid={resp['userid']}&visible=1&instance=1&_qf__core_calendar_local_event_forms_create=1",
			           "moodlewssettingfilter":"true",
			           "moodlewssettingfileurl":"true",
			           "wsfunction":"core_calendar_submit_create_update_form",
			           "wstoken":self.TOKEN}
        resp = self.session.post(url_convert,data=payload_convert)
        try:
            r = json.loads(resp.text)
            return r["event"]["description"]
        except:
            return url


    def upload_with_token(self,filename,progressfunc=None,args=None):
        try:
            data = asyncio.run(webservice_upload_file(self.path,self.TOKEN,filename,progressfunc=progressfunc,args=args,proxy=self.proxy))
            while not store_exist(filename):pass
            data = get_store(filename)
            if(data[0]!=None):
                url = make_draft_urls(data[0])[0]
                url = str(url)#.replace('draftfile.php','webservice/pluginfile.php')
                url = self.parse_calendar_with_token(data[0][0],url).replace('pluginfile.php','webservice/pluginfile.php') +'?token='+self.TOKEN 
                return url
        except:pass
        return None

    def set_cookies(self,cookies):
        self.cookies = cookies

    def get_cookies(self):
        cookies = self.session.cookies.get_dict()
        if self.cookies:
            cookies = self.cookies
        return cookies

    def getUserData(self):
        try:
            tokenUrl = self.path+'login/token.php?service=moodle_mobile_app&username='+urllib.parse.quote(self.username)+'&password='+urllib.parse.quote(self.password)
            resp = self.session.get(tokenUrl,proxies=self.proxy,headers=self.headers)
            data = self.parsejson(resp.text)
            data['s5token'] = S5Crypto.tokenize([self.username,self.password]) 
            return data
        except:
            return None

    def getDirectUrl(self,url):
        tokens = str(url).split('/')
        direct = self.path+'webservice/pluginfile.php/'+tokens[4]+'/user/private/'+tokens[-1]+'?token='+self.data['token']
        return direct

    def getSessKey(self):
        fileurl = self.path + 'my/#'
        resp = self.session.get(fileurl,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        return sesskey

    def login(self):
        try:
            self.session = requests.Session()
            login = self.path+'login/index.php'
            resp = self.session.get(login,proxies=self.proxy,headers=self.headers)
            cookie = resp.cookies.get_dict()
            soup = BeautifulSoup(resp.text,'html.parser')
            anchor = ''
            try:
              anchor = soup.find('input',attrs={'name':'anchor'})['value']
            except:pass
            logintoken = ''
            try:
                logintoken = soup.find('input',attrs={'name':'logintoken'})['value']
            except:pass
            username = self.username
            password = self.password
            payload = {'anchor': '', 'logintoken': logintoken,'username': username, 'password': password, 'rememberusername': 1}
            loginurl = self.path+'login/index.php'
            resp2 = self.session.post(loginurl, data=payload,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp2.text,'html.parser')
            counter = 0
            for i in resp2.text.splitlines():
                if "loginerrors" in i or (0 < counter <= 3):
                    counter += 1
                    print(i)
            if resp2.url==loginurl:
                counter+=1
            if counter>0:
                print('No pude iniciar sesion')
                return False
            else:
                try:
                    self.userid = soup.find('div',{'id':'nav-notification-popover-container'})['data-userid']
                except:
                    try:
                        self.userid = soup.find('a',{'title':'Enviar un mensaje'})['data-userid']
                    except:pass
                #print('E iniciado sesion con exito')
                self.loged = True
                self.userdata = self.getUserData()
                try:
                    self.sesskey  =  self.getSessKey()
                except:pass
                return True
        except Exception as ex:
            pass
        return False

    def parse_calendar(self,urls):
        today = str(datetime.date.today()).split('-')
        date = {'year':today[0],'month':today[1],'day':today[2]}
        base_url = (
                "{}/lib/ajax/service.php?sesskey={}&info=core_calendar_submit_create_update_form"
        )
        payload = [
                {
                    "index": 0,
                    "methodname": "core_calendar_submit_create_update_form",
                    "args": {
                        "formdata": "id=0&userid={}&modulename=&instance=0&visible=1&eventtype=user&sesskey={}&_qf__core_calendar_local_event_forms_create=1&mform_showmore_id_general=1&name=Subidas&timestart[day]="+date['day']+"&timestart[month]="+date['month']+"&timestart[year]="+date['year']+"&timestart[hour]=18&timestart[minute]=55&timedurationuntil[day]="+str(int(date['day'])+2)+"&timedurationuntil[month]="+date['month']+"&timedurationuntil[hour]=18&timedurationuntil[minute]=55&timedurationuntil[year]="+date['year']+"&description[text]={}&description[format]=1&description[itemid]=940353303&location=&duration=0"
                    },
                }
            ]
        urls_payload = '<p dir="ltr"><span style="font-size: 14.25px;">{}</span></p>'
        base_url = base_url.format(self.path, self.sesskey)
        urlparse = lambda url: urllib.parse.quote_plus(urls_payload.format(url))
        urls_parsed = "".join(list(map(urlparse, urls)))
        payload[0]["args"]["formdata"] = payload[0]["args"]["formdata"].format(
                self.userid, self.sesskey, urls_parsed
        )
        resp = self.session.post(base_url, data=json.dumps(payload))
        resp = json.loads(resp.text)
        resp = resp[0]["data"]["event"]["description"]
        resp = re.findall("https?://[^\s\<\>]+[a-zA-z0-9]", resp)
        finalresp = resp
        userdata = self.getUserData()
        if 'token' in userdata:
            finalresp = []
            for item in resp:
                finalresp.append(str(item).replace('pluginfile.php','webservice/pluginfile.php') + '?token=' + userdata['token']) 
        return finalresp

    def parse_profile(self,urls):
        profile = self.path + 'user/profile.php'
        resp = self.session.get(profile,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        inputs = soup.find_all('input',{'type':'hidden'})
        payload = {}
        for inp in inputs:
            payload[inp['name']] = inp['value']
        payload.pop('edit')
        payload.pop('reset')
        payload['submitbutton'] = 'Actualizar+información+personal'
        payload['imagealt'] = ''
        payload['city'] = ''
        payload['description_editor[text]'] = '<p+dir="ltr"+style="text-align:left;">{{0}}</p>'
        asubmits = ''
        for url in urls:
            add = True
            for p in self.profiles:
                if p == url:
                    add == False
                    break
            if add:
                self.profiles.append(url)
        for url in self.profiles:
            asubmits += f'<a+href="'+str(url)+'">'+str(url)+'<br/></a>'
        payload['description_editor[text]'] = str(payload['description_editor[text]']).replace('{{0}}',asubmits)
        resp = self.session.post(profile,data=payload,proxies=self.proxy,headers=self.headers)
        token = ''
        userdata = self.getUserData()
        if userdata:
            if 'token' in userdata:
                token = userdata['token']
        if resp.status_code==200:
            i=0
            for url in urls:
                name = str(url).split('/')[-1]
                url = str(url).split('/draft/')[0] + '/profile/' + name
                if token!='':
                    url = str(url).replace('draftfile.php','webservice/pluginfile.php')+'?token='+token
                urls[i] = url
                i+=1
        return urls

    def createEvidence(self,name,desc=''):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidenceurl,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')

        sesskey  =  self.sesskey
        files = self.extractQuery(soup.find('object')['data'])['itemid']



        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=&userid='+self.userid+'&return='
        payload = {'userid':self.userid,
                   'sesskey':sesskey,
                   '_qf__tool_lp_form_user_evidence':1,
                   'name':name,'description[text]':desc,
                   'description[format]':1,
                   'url':'',
                   'files':files,
                   'submitbutton':'Guardar+cambios'}
        resp = self.session.post(saveevidence,data=payload,proxies=self.proxy,headers=self.headers)

        evidenceid = str(resp.url).split('?')[1].split('=')[1]

        return {'name':name,'desc':desc,'id':evidenceid,'url':resp.url,'files':[]}

    def createBlog(self,name,itemid,desc="<p+dir=\"ltr\"+style=\"text-align:+left;\">asd<br></p>"):
        post_attach = f'{self.path}blog/edit.php?action=add&userid='+self.userid
        resp = self.session.get(post_attach,proxies=self.proxy)
        soup = BeautifulSoup(resp.text,'html.parser') 
        attachment_filemanager = soup.find('input',{'id':'id_attachment_filemanager'})['value']
        post_url = f'{self.path}blog/edit.php'
        payload = {'action':'add',
                   'entryid':'',
                   'modid':0,
                   'courseid':0,
                   'sesskey':self.sesskey,
                   '_qf__blog_edit_form':1,
                   'mform_isexpanded_id_general':1,
                   'mform_isexpanded_id_tagshdr':1,
                   'subject':name,
                   'summary_editor[text]':desc,
                   'summary_editor[format]':1,
                   'summary_editor[itemid]':itemid,
                   'attachment_filemanager':attachment_filemanager,
                   'publishstate':'site',
                   'tags':'_qf__force_multiselect_submission',
                   'submitbutton':'Guardar+cambios'}
        resp = self.session.post(post_url,data=payload,proxies=self.proxy,headers=self.headers)
        return resp



    def saveEvidence(self,evidence):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id='+evidence['id']+'&userid='+self.userid+'&return=list'
        resp = self.session.get(evidenceurl,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        files = evidence['files']
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id='+evidence['id']+'&userid='+self.userid+'&return=list'
        payload = {'userid':self.userid,
                   'sesskey':sesskey,
                   '_qf__tool_lp_form_user_evidence':1,
                   'name':evidence['name'],'description[text]':evidence['desc'],
                   'description[format]':1,'url':'',
                   'files':files,
                   'submitbutton':'Guardar+cambios'}
        resp = self.session.post(saveevidence,data=payload,proxies=self.proxy)
        return evidence

    def getEvidences(self):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid 
        resp = self.session.get(evidencesurl,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        nodes = soup.find_all('tr',{'data-region':'user-evidence-node'})
        list = []
        for n in nodes:
            nodetd = n.find_all('td')
            evurl = nodetd[0].find('a')['href']
            evname = n.find('a').next
            evid = evurl.split('?')[1].split('=')[1]
            nodefiles = nodetd[1].find_all('a')
            nfilelist = []
            for f in nodefiles:
                url = str(f['href'])
                directurl = url
                try:
                    directurl = url + '&token=' + self.userdata['token']
                    directurl = str(directurl).replace('pluginfile.php','webservice/pluginfile.php')
                except:pass
                nfilelist.append({'name':f.next,'url':url,'directurl':directurl})
            list.append({'name':evname,'desc':'','id':evid,'url':evurl,'files':nfilelist})
        return list

    def deleteEvidence(self,evidence):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidencesurl,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        deleteUrl = self.path+'lib/ajax/service.php?sesskey='+sesskey+'&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
        savejson = [{"index":0,"methodname":"core_competency_delete_user_evidence","args":{"id":evidence['id']}},
                    {"index":1,"methodname":"tool_lp_data_for_user_evidence_list_page","args":{"userid":self.userid }}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01',**self.headers}
        resp = self.session.post(deleteUrl, json=savejson,headers=headers,proxies=self.proxy)
        pass



    def upload_file(self,file,evidence=None,itemid=None,progressfunc=None,args=(),tokenize=False):
        try:
            fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self.session.get(fileurl,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text,'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            _qf__user_files_form = 1
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = self.getclientid(resp.text)
        
            itempostid = query['itemid']
            if itemid:
                itempostid = itemid

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,itempostid),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['areamaxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b,**self.headers},proxies=self.proxy)
            of.close()

            #save evidence
            if evidence:
                evidence['files'] = itempostid

            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\','')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    name = str(data['url']).split('/')[-1]
                    data['url'] = self.path+'webservice/pluginfile.php/'+query['ctx_id']+'/core_competency/userevidence/'+evidence['id']+'/'+name
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return itempostid,data
        except:
            return None,None

    def upload_file_blog(self,file,blog=None,itemid=None,progressfunc=None,args=(),tokenize=False):
        try:
            fileurl = self.path + 'blog/edit.php?action=add&userid=' + self.userid
            resp = self.session.get(fileurl,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text,'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            _qf__user_files_form = 1
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = self.getclientid(resp.text)
        
            itempostid = query['itemid']
            if itemid:
                itempostid = itemid

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,itempostid),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['areamaxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b,**self.headers},proxies=self.proxy)
            of.close()

            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\','')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/','webservice/pluginfile.php/') + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return itempostid,data
        except:
            return None,None

    def upload_file_perfil(self,file,progressfunc=None,args=(),tokenize=False):
            file_edit = f'{self.path}user/edit.php?id={self.userid}&returnto=profile'
            #https://eduvirtual.uho.edu.cu/user/profile.php
            resp = self.session.get(file_edit,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            usertext =  'ObisoftDev'
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = str(soup.find('div',{'class':'filemanager'})['id']).replace('filemanager-','')

            upload_file = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,query['itemid']),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['areamaxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b,**self.headers},proxies=self.proxy)
            of.close()
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\','')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/','webservice/pluginfile.php/')
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']

            payload = {
                'returnurl': file_edit,
                'sesskey': sesskey,
                '_qf__user_files_form': '.jpg',
                'submitbutton': 'Guardar+cambios'
            }
            resp3 = self.session.post(file_edit, data = payload)

            return None,data

    def upload_file_draft(self,file,progressfunc=None,args=(),tokenize=False):
            file_edit = f'{self.path}user/files.php'
            #https://eduvirtual.uho.edu.cu/user/profile.php
            resp = self.session.get(file_edit,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            usertext =  'ObisoftDev'
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = str(soup.find('div',{'class':'filemanager'})['id']).replace('filemanager-','')

            upload_file = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,query['itemid']),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['areamaxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            if upload_data['areamaxbytes'][1]=='0':
                upload_data['areamaxbytes'] = (None,'100000000000')
                upload_data['maxareabytes'] = (None,'100000000000')
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b,**self.headers},proxies=self.proxy)
            of.close()
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\','')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/','webservice/pluginfile.php/')
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return None,data

    def upload_file_draft_perfil(self,file,progressfunc=None,args=(),tokenize=False):
            file_edit = f'{self.path}user/files.php'
            #https://eduvirtual.uho.edu.cu/user/profile.php
            resp = self.session.get(file_edit,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            usertext =  'ObisoftDev'
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = str(soup.find('div',{'class':'filemanager'})['id']).replace('filemanager-','')

            upload_file = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,query['itemid']),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['areamaxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            if upload_data['areamaxbytes'][1]=='0':
                upload_data['areamaxbytes'] = (None,'100000000000')
                upload_data['maxareabytes'] = (None,'100000000000')
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b,**self.headers},proxies=self.proxy)
            of.close()
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\','')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/','webservice/pluginfile.php/')
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return None,data

    def upload_file_calendar(self,file,progressfunc=None,args=(),tokenize=False):
            file_edit = f'{self.path}/calendar/managesubscriptions.php'
            #https://eduvirtual.uho.edu.cu/user/profile.php
            resp = self.session.get(file_edit,proxies=self.proxy,headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey
            if self.sesskey=='':
                sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
            usertext =  'ObisoftDev'
            query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
            client_id = str(soup.find('input',{'name':'importfilechoose'})['id']).replace('filepicker-button-','')

            upload_file = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title':(None,''),
                'author':(None,'ObysoftDev'),
                'license':(None,'allrightsreserved'),
                'itemid':(None,query['itemid']),
                'repo_id':(None,str(self.repo_id)),
                'p':(None,''),
                'page':(None,''),
                'env':(None,query['env']),
                'sesskey':(None,sesskey),
                'client_id':(None,client_id),
                'maxbytes':(None,query['maxbytes']),
                'areamaxbytes':(None,query['maxbytes']),
                'ctx_id':(None,query['ctx_id']),
                'savepath':(None,'/')}
            upload_file = {
                'repo_upload_file':(file,of,'application/octet-stream'),
                **upload_data
                }
            post_file_url = self.path+'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback=callback)
            resp2 = self.session.post(post_file_url,data=monitor,headers={"Content-Type": "multipart/form-data; boundary="+b},proxies=self.proxy)
            of.close()
            print(resp2.text)
            data = self.parsejson(resp2.text)

            data['url'] = str(data['url']).replace('\\','')
            token = ""
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    #data['url'] = str(data['url']).replace('pluginfile.php/','webservice/pluginfile.php/')
                    token = self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return None,data
    
    def parsejson(self,json):
        data = {}
        tokens = str(json).replace('{','').replace('}','').split(',')
        for t in tokens:
            split = str(t).split(':',1)
            data[str(split[0]).replace('"','')] = str(split[1]).replace('"','')
        return data

    def getclientid(self,html):
        index = str(html).index('client_id')
        max = 25
        ret = html[index:(index+max)]
        return str(ret).replace('client_id":"','')

    def extractQuery(self,url):
        tokens = str(url).split('?')[1].split('&')
        retQuery = {}
        for q in tokens:
            qspl = q.split('=')
            try:
                retQuery[qspl[0]] = qspl[1]
            except:
                 retQuery[qspl[0]] = None
        return retQuery

    def getFiles(self):
        urlfiles = self.path+'user/files.php'
        resp = self.session.get(urlfiles,proxies=self.proxy,headers=self.headers)
        soup = BeautifulSoup(resp.text,'html.parser')
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        client_id = self.getclientid(resp.text)
        filepath = '/'
        query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
        payload = {'sesskey': sesskey, 'client_id': client_id,'filepath': filepath, 'itemid': query['itemid']}
        postfiles = self.path+'repository/draftfiles_ajax.php?action=list'
        resp = self.session.post(postfiles,data=payload,proxies=self.proxy,headers=self.headers)
        dec = json.JSONDecoder()
        jsondec = dec.decode(resp.text)
        return jsondec['list']
   
    def delteFile(self,url):
        urlfiles = self.path+'user/files.php'
        resp = self.session.get(urlfiles,proxies=self.proxy,headers=self.headers,cookies=self.cookies)
        soup = BeautifulSoup(resp.text,'html.parser')
        _qf__core_user_form_private_files = soup.find('input',{'name':'_qf__core_user_form_private_files'})['value']
        files_filemanager = soup.find('input',attrs={'name':'files_filemanager'})['value']
        sesskey  =  soup.find('input',attrs={'name':'sesskey'})['value']
        client_id = self.getclientid(resp.text)
        filepath = '/'
        itemid = url.split('/')[-2]
        name = url.split('/')[-1]
        query = self.extractQuery(soup.find('object',attrs={'type':'text/html'})['data'])
        payload = {'sesskey': sesskey, 'client_id': client_id,'filepath': filepath, 'itemid': itemid,'filename':name}
        postdelete = self.path+'repository/draftfiles_ajax.php?action=delete'
        resp = self.session.post(postdelete,data=payload,proxies=self.proxy,headers=self.headers,cookies=self.cookies)

        #save file
        saveUrl = self.path+'lib/ajax/service.php?sesskey='+sesskey+'&info=core_form_dynamic_form'
        savejson = [{"index":0,"methodname":"core_form_dynamic_form","args":{"formdata":"sesskey="+sesskey+"&_qf__core_user_form_private_files="+_qf__core_user_form_private_files+"&files_filemanager="+query['itemid']+"","form":"core_user\\form\\private_files"}}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01',**self.headers}
        resp3 = self.session.post(saveUrl, json=savejson,headers=headers,proxies=self.proxy)

        return resp3

    def delete_file(self,file_url):
        delete_url = f"{self.host}webservice/rest/server.php?file={file_url}"
        headers = {
            "Authorization": "Bearer tu_token_de_acceso",
            "Content-Type": "application/json"
        }

        # Realizar la solicitud DELETE para eliminar el archivo
        response = self.session.Request('DELETE',delete_url, headers=headers)

        if response.status_code == 200:
            print("Archivo eliminado exitosamente.")
        else:
            print("Hubo un error al intentar eliminar el archivo.")

    def logout(self):
        logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
        self.session.post(logouturl,proxies=self.proxy,headers=self.headers)


#client = MoodleClient('adianez.torres','Y@svel911025.','https://eva.uo.edu.cu/',repo_id=4)
#loged = client.login()
#if loged:
#	print('loges')
#	resp,data = client.upload_file_draft('requirements.txt')
#	print(data)
#    resp,data2 = client.upload_file_calendar('mediafire.py')
#    print(data2)
#    print('parsing profile...')
#    parsed = client.parse_profile([data['url'],data2['url']])
#    print(parsed)
#    client.createBlog('req',data['id'])
#   print(data)
#   list = client.getEvidences()
#   evidence = client.createEvidence('requirements')
#   client.upload_file('requirements.txt',evidence,progressfunc=uploadProgres)
#   client.saveEvidence(evidence)
#   print(evidence)