import requests
import os
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import time
from bs4 import BeautifulSoup
from ProxyCloud import ProxyCloud
from urllib.parse import unquote
from pyobigram.readers import FileProgressReader

import socket
import socks
import json
import S5Crypto
import uuid
import xmltodict

class NexCloudClient(object):
    def __init__(self, user,password,path='https://nube.uo.edu.cu/',proxy:ProxyCloud=None):
        self.username = user
        self.password = password
        self.session = requests.Session()
        self.path = path
        self.tokenize_host = 'https://tguploader.url/'
        self.proxy = None
        if proxy:
            self.proxy = proxy.as_dict_proxy()
        self.data_user = None
        self.csrf = None
        self.loged = False
        self.cookies = None

    def getsession(self):
        return self.session

    def get_cookies(self):
        cookies = self.session.cookies.get_dict()
        if self.cookies:
            cookies = self.cookies
        return cookies

    def set_cookies(self,cookies):
        self.cookies = cookies

    def login(self):
        self.session = requests.Session()
        loginurl = self.path + 'index.php/login'
        resp = self.session.get(loginurl,proxies=self.proxy,cookies=self.cookies)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        timezone = 'America/Mexico_City'
        timezone_offset = '-5'
        payload = {'user':self.username,'password':self.password,'timezone':timezone,'timezone_offset':timezone_offset,'requesttoken':requesttoken};
        resp = self.session.post(loginurl, data=payload,proxies=self.proxy,cookies=self.cookies)
        soup = BeautifulSoup(resp.text,'html.parser')
        title = soup.find('title').next
        if resp.url != loginurl:
            print('E Iniciado Correctamente')
            self.loged = True
            soup = BeautifulSoup(resp.text, 'html.parser')
            self.data_user = soup.find('head')['data-user']
            self.csrf = soup.find('head')['data-requesttoken']
            return True
        self.loged = False
        return False

    def in_loged(self):
        try:
            files = self.path + 'index.php/apps/files/'
            resp = self.session.get(files,proxies=self.proxy,cookies=self.cookies)
            soup = BeautifulSoup(resp.text,'html.parser')
            title = soup.find('title').next
            if 'Archivos - Nube' in title:
                self.loged = True
                soup = BeautifulSoup(resp.text, 'html.parser')
                self.data_user = soup.find('head')['data-user']
                self.csrf = soup.find('head')['data-requesttoken']
                return True
        except:pass
        return False

    def upload_file(self,file,path='',progressfunc=None,args=(),tokenize=False):
        files = self.path + 'index.php/apps/files/'
        filepath = str(file).split('/')[-1]
        uploadUrl = self.path + 'remote.php/webdav/'+ path + filepath
        resp = self.session.get(files)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        f  = FileProgressReader(file,progress_func=progressfunc,progress_args=args,self_in=self)
        upload_file = {'file':(file,f,'application/octet-stream')}
        hdrs = {
            'requesttoken':requesttoken
            }
        resp = self.session.put(uploadUrl,data=f,headers=hdrs,proxies=self.proxy,stream=True,cookies=self.cookies)
        f.close()
        retData = {'upload':False,'name':filepath}
        if resp.status_code == 201:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':True,'name':filepath,'msg':file + ' Upload Complete!','url':url}
        if resp.status_code == 204:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':False,'name':filepath,'msg':file + ' Exist!','url':url}
        if resp.status_code == 409:
            retData = {'upload':False,'msg':'Not ' + user + ' Folder Existent!','name':filepath}
        return retData

    def upload_file_to_uploads(self,file,folder=None,progressfunc=None,args=None,tokenize=False):
        files = self.path + 'index.php/apps/files/'
        filepath = str(file).split('/')[-1]
        resp = self.session.get(files,proxies=self.proxy,cookies=self.cookies)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        headers = {'requesttoken':requesttoken}
        folder_name = f'/webfile-upload-{uuid.uuid1()}/'
        if folder:
            folder_name = folder
        response = self.session.request('MKCOL', f'{self.path}remote.php/dav/uploads/{self.data_user}{folder_name}',cookies=self.cookies,proxies=self.proxy, headers=headers, allow_redirects=False)
        uploadUrl = self.path + f'remote.php/dav/uploads/{self.data_user}{folder_name}{file}'
        f  = FileProgressReader(file,progress_func=progressfunc,progress_args=args,self_in=self)
        upload_file = {'file':(file,f,'application/octet-stream')}
        hdrs = {
            'requesttoken':requesttoken
            }
        resp = self.session.put(uploadUrl,data=f,headers=hdrs,proxies=self.proxy,stream=True,cookies=self.cookies)
        f.close()
        retData = {'upload':False,'name':filepath}
        if resp.status_code == 201:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':True,'name':filepath,'msg':file + ' Upload Complete!','url':url}
        if resp.status_code == 204:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':False,'name':filepath,'msg':file + ' Exist!','url':url}
        if resp.status_code == 409:
            retData = {'upload':False,'msg':'Not ' + user + ' Folder Existent!','name':filepath}
        return folder_name,retData

    def delete_uploads(self,url):
        folder_name = url.split('/')[-2]
        headers = {'requesttoken':self.csrf}
        response = self.session.request('DELETE', f'{self.path}remote.php/dav/uploads/{self.data_user}/{folder_name}', headers=headers, allow_redirects=False)
        if response.status_code==200 or response.status_code == 204:
            return True
        return False

    def upload_file_chunked(self,file,path='',chunk=1024):
        queda = True;
        mvurl = ''
        i = 0
        while True:
            with open(file,'rb') as fi:
                i+=1
                data = fi.read(chunk)
                if len(data)<=0:break
                tmpname = f'temp{i}.tmp'
                filetemp = open(tmpname,'wb')
                filetemp.write(data)
                filetemp.close()
                result = self.upload_file(tmpname,path)
                if 'url' in result:
                    if queda:
                        mvurl = result['url']
                        queda = False
                    else:
                        headers = {'Destination': mvurl}
                        req = self.session.request(
                        'MOVE',
                        result['url'],
                        headers=headers,
                        )
                        print(req)
        return mvurl


    

    def share(self,pathfile='',password=''):
        files = self.path + 'index.php/apps/files/'
        resp = self.session.get(files, proxies=self.proxy,cookies=self.cookies)
        soup = BeautifulSoup(resp.text, 'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        shareurl = None
        shareurl = self.path+'ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'
        passwordchanged = 'false'
        if password!='':
            passwordchanged = 'true'
        payload = {
            "password": password,
            "passwordChanged": passwordchanged,
            "permissions": "19",
            "expireDate": "",
            "shareType": "3",
            "path": "/" + pathfile
        }
        resp = self.session.post(shareurl,data=payload,proxies=self.proxy,cookies=self.cookies,headers={'requesttoken':requesttoken,'OCS-APIREQUEST':'true'})
        try:
            jsondata = json.loads(resp.text)
            shareurl = jsondata['ocs']['data']['url'] + '/download'
        except:
            print(str(ex))
        return shareurl

    def share_from(self,url='',password=''):
        files = self.path + 'index.php/apps/files/'
        resp = self.session.get(files, proxies=self.proxy,cookies=self.cookies)
        soup = BeautifulSoup(resp.text, 'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        shareurl = None
        shareurl = self.path+'ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'
        passwordchanged = 'false'
        if password!='':
            passwordchanged = 'true'
        payload = {
            "password": password,
            "passwordChanged": passwordchanged,
            "permissions": "31",
            "expireDate": "",
            "shareType": "0",
            "path": "/" + url.replace(self.path,'').replace('/'+url.split('/')[-1],'')
        }
        resp = self.session.post(shareurl,data=payload,proxies=self.proxy,headers={'requesttoken':requesttoken,'OCS-APIREQUEST':'true'})
        try:
            jsondata = json.loads(resp.text)
            shareurl = jsondata['ocs']['data']['url'] + '/download'
        except:
            print(str(ex))
        return shareurl

    def get_quote(self):
        try:
            files = self.path + 'index.php/apps/files/'
            resp = self.session.get(files, proxies=self.proxy,cookies=self.cookies)
            soup = BeautifulSoup(resp.text, 'html.parser')
            quotetext = soup.find('p',{'id':'quotatext'}).next
            return str(quotetext).replace('usados','total').replace('de','usados /')
        except:pass
        return "0 MB de 2 GB usados"


    def delete(self,pathfile):
        deleteurl = f'{self.path}remote.php/webdav/{pathfile}'
        req = requests.request('DELETE', deleteurl,proxies=self.proxy,auth=(self.username,self.password))
        return

    def get_root(self,path=''):
        result = {}
        root = self.path + 'remote.php/webdav/' + path
        webdav_options = '<?xml version="1.0"?><d:propfind  xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><d:getlastmodified /><d:getetag /><d:getcontenttype /><d:resourcetype /><oc:fileid /><oc:permissions /><oc:size /><d:getcontentlength /><oc:tags /><oc:favorite /><oc:owner-display-name /><oc:share-types /><oc:comments-unread /></d:prop></d:propfind>'
        req = requests.request('PROPFIND', root,proxies=self.proxy,cookies=self.cookies,auth=(self.user,self.password),data=webdav_options,headers={'Depth':'1'})
        xml_dict = xmltodict.parse(req.text, dict_constructor=dict)
        for response in xml_dict['d:multistatus']['d:response']:
            try:
                filename = unquote(response['d:href']).split('/')[-1]
                if filename=='': continue
                fileurl = self.path + unquote(response['d:href'])
                fileurl = fileurl.replace('//','/')
                fileurl = fileurl.replace('https:/','https://')
                fileurl = fileurl.replace('http:/','http://')
                if filename:
                    result[filename] = fileurl
            except:pass
        return result

    def get_trash_root(self):
        result = {}
        root = self.path + f'remote.php/dav/trashbin/{self.data_user}/trash'
        webdav_options = '<?xml version="1.0"?><d:propfind  xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><d:getlastmodified /><d:getetag /><d:getcontenttype /><d:resourcetype /><oc:fileid /><oc:permissions /><oc:size /><d:getcontentlength /><oc:tags /><oc:favorite /><oc:owner-display-name /><oc:share-types /><oc:comments-unread /></d:prop></d:propfind>'
        req = requests.request('PROPFIND', root,proxies=self.proxy,cookies=self.cookies,auth=(self.username,self.password),data=webdav_options,headers={'Depth':'1'})
        xml_dict = xmltodict.parse(req.text, dict_constructor=dict)
        for response in xml_dict['d:multistatus']['d:response']:
            try:
                filename = unquote(response['d:href']).split('/')[-1]
                if filename=='': continue
                fileurl = self.path + unquote(response['d:href'])
                fileurl = fileurl.replace('//','/')
                fileurl = fileurl.replace('https:/','https://')
                fileurl = fileurl.replace('http:/','http://')
                if filename:
                    result[filename] = fileurl
            except:pass
        return result

    def upload_file_trash(self,file,progressfunc=None,args=(),tokenize=False):
        try:
            resp = self.upload_file(file,progressfunc=progressfunc,args=args,tokenize=tokenize)
            if 'url' in resp:
                self.delete(file)
                trash = self.get_trash_root()
                for fi in trash:
                    if file in fi:
                        return {'filename':fi,'url':trash[fi]}
        except:pass
        return None


#proxy = ProxyCloud('181.225.253.17',4545)
#try:
#    client = NexCloudClient('pedro.bardaji','PBpB85gd9V*')
#    loged = client.login()
#    if loged:
#        print('loged!')
#        print(client.get_quote())
#        print(os.listdir())
#        data = client.upload_file('requirements.txt')
#        print(data)
#    else:
#        print('Not loged!')
#except Exception as ex:
#    print(str(ex))
#input()