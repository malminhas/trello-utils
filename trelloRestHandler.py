#!/usr/bin/env python
#
# trelloRestHandler.py
# --------------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#

import requests
import os

class TrelloRESTHandler(object):
    def __init__(self,root):
        self.root = root

    def getKey(self,keyFile,credType):
        if os.path.exists(keyFile):
            with open(keyFile,'r') as f:
                key = f.read()
                assert(len(key))
        else:
            key = input('{} key: '.format(credType))
            with open(keyFile,'w') as f:
                f.write(key)
        return key

    def getToken(self,tokenFile,credType):
        if os.path.exists(tokenFile):
            with open(tokenFile,'r') as f:
                token = f.read()
                assert(len(token))
        else:
            token = getpass.getpass('{} token:'.format(credType))
            with open(tokenFile,'w') as f:
                f.write(token)
        return token

    def setupKeyAndToken(self,keyFile,tokenFile,credType):
        return self.getKey(keyFile,credType), self.getToken(tokenFile,credType)

    def getRequest(self,command,headers={},params={},verbose=True):
        #auth = requests.auth.HTTPBasicAuth(username,password)
        url = '{}/{}'.format(self.root,command)
        custom_headers = {'Accept': 'application/json','Content-Type': 'application/json'}
        custom_headers = {**custom_headers,**headers}
        req = requests.Request('GET',url,params=params,headers=custom_headers)
        prepared = req.prepare()
        verbose and self.dumpRequest(prepared,isPost=False)
        s = requests.Session()
        try:
            r = s.send(prepared)
            verbose and self.dumpResponse(r)
        except e:
            print("Failed: '{}'".format(e))
        return r

    def postRequest(self,command,body='',headers={},verbose=False):
        #auth = requests.auth.HTTPBasicAuth(username,password)
        url = '{}/{}'.format(self.root,command)
        custom_headers = {'Accept': 'application/json','Content-Type': 'application/json'}
        custom_headers = {**custom_headers,**headers}
        req = requests.Request('POST',url,headers=custom_headers,data=body)
        prepared = req.prepare()
        verbose and self.dumpRequest(prepared,isPost=True)
        s = requests.Session()
        try:
            r = s.send(prepared)
            verbose and self.dumpResponse(r)
        except e:
            print("Failed: '{}'".format(e))
        return r

    def dumpRequest(self,request,isPost):
        """
        The request is built and "prepared" to be fired at this point.   Note the 
        pretty print formatting is intended to be visually easy to understand. 
        It may differ from the actual request structure.
        """
        if isPost:
            print('{}\n{}\n{}\n\n{}'.format(
                '----------- POST REQUEST-----------',
                request.method + ' ' + request.url,
                '\n'.join('{}: {}'.format(k, v) for k, v in request.headers.items()),
                request.body,
            ))
        else:
            print('{}\n{}\n{}'.format(
                '----------- GET REQUEST-----------',
                request.method + ' ' + request.url,
                '\n'.join('{}: {}'.format(k, v) for k, v in request.headers.items()),
            ))
            
    def dumpResponse(self,response):
        print('{}'.format('-----------RESPONSE-----------'))
        print("status_code={}, reason={}".format(response.status_code,response.reason))
        print('RESPONSE {}\n{}'.format(response.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in response.headers.items())
        ))
        if response.status_code in [200]:
            print("\n{}".format(response.text))


