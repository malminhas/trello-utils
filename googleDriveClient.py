#!/usr/bin/env python
#
# googleDriveClient.py
# --------------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#
# Setup and Installation
# ----------------------
# 1. Starting point is a Python 3 environment with virtualenvwrapper configured.
# There are numerous resources online for how to do that such as:
# https://medium.com/@gitudaniel/installing-virtualenvwrapper-for-python3-ad3dfea7c717
# 2. Once virtualenv is setup you create a venv and transition to it thus:
# $ mkvirtualenv gdrive 
# $ workon gdrive
# (gdrive) $ pip install -r requirements.txt
# 3. Check you have the right versions of PyDrive installed:
# (gdrive) $ pip freeze | grep -E "PyDrive"
# PyDrive==1.3.1
# 4. Configure your Google Drive credentials using the recipe outlined here:
# https://developers.google.com/drive/api/v3/quickstart/python
# 5. Run this script in standalone mode to setup the OAuth credentials:
# (gdrive) $ python googleDriveClient.py
#

import os
from googleDriveHandler import GoogleDriveHandler
GDRIVE_CLIENT_ID_FILE       = '.googleclientid'
GDRIVE_CLIENT_SECRET_FILE   = '.googleclientsecret'

class GoogleDriveClient(object):
    def __init__(self,handler,verbose=False):
        self.verbose = verbose
        self.handler = handler
        gclientid,gsecret = self.handler.setupKeyAndToken(GDRIVE_CLIENT_ID_FILE,GDRIVE_CLIENT_SECRET_FILE,'google')
        assert(len(gclientid) == 72)
        assert(len(gsecret) == 24)
        self.handler.createSettingsYaml(gclientid,gsecret)
        self.drive = self.handler.getGoogleDriveInstance()

    def getFiles(self, folder_id='root', filters=''):
        '''
        drive: authenticated GoogleDrive instance
        folder_id: uid for folder (see: https://stackoverflow.com/questions/40224559/list-of-file-in-a-folder-drive-api-pydrive/40236586)
        filters: search string to limit files returned
        '''
        l = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
        files = [item for item in l if item.get('mimeType') != 'application/vnd.google-apps.folder' and filters in item.get('title')]
        return files

    def getFileList(self,folder_id='root',filters=''):
        files = self.getFiles(folder_id,filters)
        return [{'title':item.get('title'),'mime_type':item.get('mimeType'),'id':item.get('id')} for item in files]

    def uploadFile(self, name, mimeType='',permType='user',permValue='user',permRole='owner'):
        '''
        name: name of a local file
        permType: user|group|domain|anyone
        permRole: owner|organizer|fileOrganizer|writer|reader|writable
        returns: shareable link
        '''
        assert(os.path.exists(name))
        file = self.drive.CreateFile({'title':name, 'mimeType':mimeType})
        file.SetContentFile(name)
        file.Upload()
        permission = file.InsertPermission({
                            'type': permType,
                            'value': permValue,
                            'role': permRole})
        print("Uploaded '{}' with id={}".format(file.get('title'),file.get('id')))
        return file.get('id'),file.get('alternateLink')

    def createAndUploadFile(self, name, content, mimeType=''):
        file = self.drive.CreateFile({'title':name, 'mimeType':mimeType})
        file.SetContentString(content)
        file.Upload()
        return file.get('id')

    def deleteFilesById(self,ids):
        files = self.getFiles()
        for item in files:
            if item.get('id') in ids:
                try:
                    print('Deleting {} id={}'.format(item.get('title'),item.get('id')))
                    item.auth.service.files().delete(fileId=item.get('id').execute())
                except Exception as e:
                    print('An error occurred deleting "{}": {}'.format(item.get('title'), e))

    def deleteFilesByName(self,names):
        files = self.getFiles()
        for item in files:
            if item.get('title') in names:
                try:
                    print('Deleting {} id={}'.format(item.get('title'),item.get('id')))
                    item.auth.service.files().delete(fileId=item.get('id').execute())
                except Exception as e:
                    print('An error occurred deleting "{}": {}'.format(item.get('title'), e))

    def getExistingFileContent(self,id):
        assert(self.drive)
        file = self.drive.CreateFile({'id':id})
        content = file.GetContentString()
        return content

    def updateExistingFileContent(self, id, content):
        assert(self.drive)
        file = self.drive.CreateFile({'id':id})
        # How to update contents of an existing file
        file.SetContentString(content)
        file.Upload() # Update content of the file.
        return file.get('id')

    def uploadFileById(self, name, id, permType='user',permValue='user',permRole='owner'):
        '''
        name: name of a local file
        permType: user|group|domain|anyone
        permRole: owner|organizer|fileOrganizer|writer|reader|writable
        returns: shareable link
        '''
        assert(self.drive)
        assert(os.path.exists(name))
        file = self.drive.CreateFile({'id':id})
        file.SetContentFile(name)
        file.Upload()
        permission = file.InsertPermission({
                            'type': permType,
                            'value': permValue,
                            'role': permRole})
        print("Updated '{}' with id={}".format(file.get('title'),file.get('id')))
        return file.get('id'),file.get('alternateLink')

if __name__ == '__main__':
    handler = GoogleDriveHandler('google_credentials')
    gdrive = GoogleDriveClient(handler)
    print("Retrieved gdrive instance: '{}'".format(gdrive))
