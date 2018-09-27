#!/usr/bin/env python
#
# trelloClient.py
# ---------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#

import requests

TRELLO_KEY_FILE     = '.ttrellokey'
TRELLO_TOKEN_FILE   = '.ttrellotoken'

class TrelloClient(object):
    def __init__(self,handler,verbose=False):
        self.handler = handler
        self.verbose = verbose
        self.apiKey,self.apiToken = self.handler.setupKeyAndToken(TRELLO_KEY_FILE,TRELLO_TOKEN_FILE,'trello')
        assert(len(self.apiKey) == 32)
        assert(len(self.apiToken) == 64)

    def getBoards(self):
        params = {'key':self.apiKey,'token':self.apiToken}
        r = self.handler.getRequest('members/me/boards', params=params, verbose=self.verbose)
        boards = r.json()
        return boards

    def getBoardByName(self, target):
        targetId = None
        targetName = None
        boards = self.getBoards()        
        for board in boards:
            if target in board.get('name'):
                targetId = board.get('id')
                targetName = board.get('name')
        return targetId,targetName

    def getLists(self, boardId):
        command = 'boards/{}/lists'.format(boardId)
        params = {'key':self.apiKey,'token':self.apiToken}
        r = self.handler.getRequest(command, params=params, verbose=self.verbose)
        lists = r.json()
        return lists

    def getCardsByList(self, listId):
        command = 'lists/{}/cards'.format(listId) # gets all fields
        params = {'key':self.apiKey,'token':self.apiToken}
        r = self.handler.getRequest(command,params=params,verbose=self.verbose)
        cards = r.json()
        return cards

    def getActionsByList(self, lists):
        '''
        Returns: single flat array of all actions by list
        '''
        lsts = [(ls.get('id'),ls.get('name')) for ls in lists]
        arr = []
        limit = 1000
        for ls in lsts:
            listid,listname = ls
            command = 'lists/{}/actions'.format(listid) # gets all actions for P1ListId
            params = {'key':self.apiKey,'token':self.apiToken,'limit':limit}
            r = self.handler.getRequest(command,params=params,verbose=False)
            actions = r.json()
            [arr.append(action) for action in actions]
            self.verbose and print("{} actions found on list '{}'".format(len(actions),listname))
        return arr

    def getActionsByCard(self,cardIds):
        '''
        Returns: single flat array of all actions by cardId
        '''
        arr = []
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i+n]
        g = chunks(cardIds,10)
        batches = list(g)
        for i,batch in enumerate(batches):
            if self.verbose:
                print("\tbatch {} of {}".format(i+1,len(batches)))
            else:
                print('.', end='', flush=True)
            # Note use of Trello batch API
            s = ','.join(['/cards/{}/actions?filter=all'.format(id) for id in batch])
            params = {'urls':s,'key':self.apiKey,'token':self.apiToken}
            r = self.handler.getRequest('batch/',params=params,verbose=self.verbose)
            results = r.json()
            for result in results:
                actions = result.get('200')
                if actions:
                    [arr.append(action) for action in actions]
        print("Completed {} batches".format(len(batches)))
        return arr
