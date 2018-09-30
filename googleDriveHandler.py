#!/usr/bin/env python
#
# googleDriveHandler.py
# --------------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import logging
import requests
import os

class GoogleDriveHandler(object):
    def __init__(self,cred_file):
        self.cred_file = cred_file
        self.settings = None
        self.settingsfile = 'settings.yaml'
        self.drive = None

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

    def createSettingsYaml(self,gclientid,gsecret):
        if os.path.exists(self.settingsfile):
            print('Using existing {}'.format(self.settingsfile))
        else:
            self.settings = '''
client_config_backend: settings
client_config:
  client_id: {}
  client_secret: {}
  auth_uri: https://accounts.google.com/o/oauth2/auth
  token_uri: https://accounts.google.com/o/oauth2/token
  redirect_uri: http://localhost:8080/
save_credentials: True
save_credentials_file: {}
save_credentials_backend: file
get_refresh_token: True
            '''.format(gclientid, gsecret, self.cred_file)
            with open('settings.yaml', 'wb') as fh:
                fh.write(self.settings.encode('utf-8'))

    def getGoogleDriveInstance(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        gauth.LoadCredentials()
        if gauth.access_token_expired:
            gauth.Refresh()
        self.drive = GoogleDrive(gauth)
        # The following disables annoying warning ref. discovery_cache
        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
        return self.drive
