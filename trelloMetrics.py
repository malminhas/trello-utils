#!/usr/bin/env python
#
# trelloMetrics.py
# ----------------
# Script to generate metrics data from Trello Boards.
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
#
# Installation:
# ------------
# $ pip install -r requirements.txt
#

import sys, os, getpass
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import cm
import seaborn as sns
# use Seaborn styles
sns.set()

PROGRAM             = __file__
VERSION             = '0.1'
TRELLO_KEY_FILE     = '.ttrellokey'
TRELLO_TOKEN_FILE   = '.ttrellotoken'

import arrow
import datetime
formatDateTime = lambda s: arrow.get(s).format('YYYY-MM-DD HH:mm:ss')
camelCase = lambda s: ''.join(x for x in s.title() if not x.isspace())

class RESTHandler(object):
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


class TrelloDataProcessor(object):
    def __init__(self,force,verbose=False):
        self.verbose = verbose
        self.force = force
        self.start = None
        self.cards = None
        self.counts = None
        if os.path.exists('cards.csv'):
            self.cards = pd.read_csv('cards.csv')
        if os.path.exists('counts.csv'):
            self.counts = pd.read_csv('counts.csv')

    def getCards(self):
        return self.cards

    def getCounts(self):
        return self.counts

    def getStart(self):
        start = None
        if os.path.exists('.start'):
            with open('.start','r') as f:
                start = f.read()
        return start

    def setStart(self,start):
        with open('.start','w') as f:
            f.write(start)

    def createCardDistributionBarChart(self, cards, desc, colors=None, reverse=False, output=None):
        df = pd.DataFrame(cards)
        if self.force or not os.path.exists('cards.csv'):
            df.to_csv('cards.csv')
        print("{} rows, {} columns".format(df.shape[0],df.shape[1]))
        gps = df.groupby(['list'])
        longest = 0
        for i,gp in enumerate(gps):
            self.verbose and print("{:02d} cards in '{}'".format(len(gp[1]),gp[0]))
            longest = max(longest,len(gp[1]))
        nrows = i+1
        longest += int(longest/20)
        self.verbose and print("longest value={}".format(longest))
        today = arrow.utcnow().format("YYYY-MM-DD")
        if reverse:
            buckets = df.groupby(['list']).size()[::-1]
            colors = colors[::-1]
        else:
            buckets = df.groupby(['list']).size()
        if (nrows != len(colors)):
            print("Mismatch between number of colors {} and number of rows {} in graph!".format(len(colors),nrows))
        cmap = cm.get_cmap('jet') 
        if longest > 50:
            if colors:
                ax = buckets.plot(kind='barh',color=colors,title='Current {} distribution {}'.format(desc,today),figsize=(18,9))
            else:
                ax = buckets.plot(kind='barh',cmap=cmap,title='Current {} distribution {}'.format(desc,today),figsize=(18,9))
        else:
            if colors:
                ax = buckets.plot(kind='barh',xticks=list(range(0,longest)),color=colors,title='Current {} distribution {}'.format(desc,today),figsize=(18,9))
            else:
                ax = buckets.plot(kind='barh',xticks=list(range(0,longest)),cmap=cmap,title='Current {} distribution {}'.format(desc,today),figsize=(18,9))
            ax.set_xticklabels(list(range(0,longest)))
        ax.set_ylabel('Trello List')
        ax.set_xlabel('count')
        if output:
            name = output
        else:
            name = '{}Snapshot_{}.png'.format(desc, today)
        plt.savefig(name)
        return name

    def createCardTimeSeriesStackedBarChart(self, counts, desc, selected, start, end=None, colors=None, output=None):
        df = pd.DataFrame(counts)
        if self.force or not os.path.exists('counts.csv'):
            df.to_csv('counts.csv')
        df.date = pd.to_datetime(df.date)
        datetimeArr = list(map(formatDateTime,df['date'].tolist()))
        # Set index of df to 'date' column and then delete 
        df.index = df['date']
        df = df.drop(columns=['date'])
        print("{} rows, {} columns".format(df.shape[0],df.shape[1]))
        print("Start date = {}".format(start))
        print("Colors: {}".format(colors))
        assert(len(counts) == df.shape[0])
        today = arrow.utcnow().format("YYYY-MM-DD")
        if not len(selected):
            # We will select ALL lists
            selected = df.columns.values.tolist()
        #if not len(colors):
        #    # We want to create a random distribution per discussion here:
        #    # https://matplotlib.org/users/dflt_style_changes.html#colors-color-cycles-and-color-maps
        #    #colors = 'bgrcmyk'  # classic
        #    colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'] # v2.0 default
        if colors[0] in ['summer','autumn','winter','spring','cool']:
            cmap = cm.get_cmap(colors[0])
            colors = None
        if df.shape[0] > 50:
            print('Greater than 50 date values!')
            # More than 50 dates to plot => need to switch to default xaxis handling
            if colors:
                ax = df[selected].plot(kind='bar',stacked=True,color=colors,xticks=df.index,
                    title='{} Board time series {}'.format(desc,today),figsize=(18,9))
            else:
                ax = df[selected].plot(kind='bar',stacked=True,cmap=cmap,xticks=df.index,
                    title='{} Board time series {}'.format(desc,today),figsize=(18,9))                    
            #ax.xaxis_date()
            # Make most of the ticklabels empty so the labels don't get too crowded
            ticklabels = ['']*len(df.index)
            # Every 4th ticklable shows the month and day
            #ticklabels[::4] = [item.strftime('%b %d') for item in df.index[::4]]
            # Every 12th ticklabel includes the year
            ticklabels[::12] = [item.strftime('%d-%m-%Y') for item in df.index[::12]]
            ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))
            plt.xticks(rotation=90)
            #plt.gcf().autofmt_xdate()
        else:
            if colors:
                ax = df[selected].plot(kind='bar',stacked=True,color=colors,xticks=df.index,
                    title='{} time series {}'.format(desc,today),figsize=(18,9))
            else:
                ax = df[selected].plot(kind='bar',stacked=True,cmap=cmap,xticks=df.index,
                    title='{} time series {}'.format(desc,today),figsize=(18,9))
            # Not using this any more - going with ticklabels approach
            #ax.set_xticklabels(datetimeArr)
            #
            #ax.xaxis_date()
            # Make most of the ticklabels empty so the labels don't get too crowded
            ticklabels = ['']*len(df.index)
            # Every 4th ticklable shows the month and day
            #ticklabels[::4] = [item.strftime('%b %d') for item in df.index[::4]]
            # Every 12th ticklabel includes the year
            ticklabels = [item.strftime('%d-%m-%Y') for item in df.index]
            ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))
            plt.xticks(rotation=90)

        ax.set_ylabel('count')
        # TBD: handling of annotations
        #ax.annotate(selected[0], xy=(start,0), color=colors[0], xytext=(start,27),fontsize=12)
        #ax.annotate(selected[1], xy=(start,0), color=colors[1],xytext=(start,7),fontsize=12)
        #ax.annotate(selected[2], xy=(start,0), color=colors[2],xytext=(start,10),fontsize=12)
        #ax.annotate(selected[3], xy=(start,0), color=colors[3],xytext=(start,3),fontsize=12)
        #ax.annotate(selected[3], xy=(start,0), color=colors[3],xytext=(start,3),fontsize=12)
        #
        #featurecomplete = "2018-08-31 21:00:00"
        #ax.plot(kind='line')
        #ax.axvline(x=featurecomplete, ymin=0, ymax=40, linestyle=':',color='k')
        #
        if output:
            name = output
        else:
            name = '{}TimeSeries_{}.png'.format(desc,today)
        plt.subplots_adjust(bottom=0.4) # Provides margin at bottom to accommodate axis
        plt.savefig(name)
        return name

    def getCardCounts(self,df,dt):
        qfilter = "category=='updateCard' or category=='createCard' or category=='deleteCard' or category=='moveCardToBoard'"
        if not dt:
            dt = formatDateTime(datetime.datetime.now())
            #today = arrow.utcnow().format("YYYY-MM-DD")
        candidates = df[df.date <= dt].query(qfilter)
        deduped = candidates.drop_duplicates(subset='card',keep='first').drop_duplicates(subset='date',keep='first')
        countsDico = deduped[deduped.closed==False].groupby(['after']).size().to_dict()
        return countsDico

    def generateDateRange(self,start,end=None):
        if not end:
            end = formatDateTime(datetime.datetime.now())
        print(start,end)
        count = 0
        drange = []
        # convert start to a datetime
        dt = arrow.get(start).datetime
        et = arrow.get(end).datetime
        drange.append(start)    
        while dt < et:
            dt = arrow.get(dt).datetime + datetime.timedelta(days=1)
            day = formatDateTime(dt)
            drange.append(formatDateTime(day))
            count += 1
        return drange

    def getActionCountsOverTime(self,actions,start,end=None):
        counts = []
        df = pd.DataFrame(actions)
        print("{} rows, {} columns".format(df.shape[0],df.shape[1]))
        df.date = pd.to_datetime(df.date)
        df.card = df.card.fillna(-1).astype(int)
        #df.list = ndf.list.astype('category')
        df.category = df.category.astype('category')
        df.board = df.board.astype('category')
        df.after = df.after.astype('category')
        df.actor = df.actor.astype('category')
        dts = self.generateDateRange(start,end)
        for dt in dts:
            dico = self.getCardCounts(df,dt)
            dico['date'] = dt
            counts.append(dico)
        assert(len(counts) == len(dts))
        return counts


def findUniqueCardIdsForActions(actions):
    cardIds = set([])
    for action in actions:
        cardId = action.get('data').get('card') and action.get('data').get('card').get('id')
        if cardId:
            cardIds.add(cardId)
    return list(cardIds)

def createActionDict(action):
    d = {}
    d['action_id'] = action.get('id')
    d['board'] = action.get('data').get('board').get('name')
    d['before'] = action.get('data').get('listBefore') and action.get('data').get('listBefore').get('name')
    d['after'] = action.get('data').get('listAfter') and action.get('data').get('listAfter').get('name')
    if not d.get('after'):
        d['after'] = action.get('data').get('list') and action.get('data').get('list').get('name')
    d['card'] = action.get('data').get('card') and action.get('data').get('card').get('idShort')
    d['old'] = action.get('data').get('old') and action.get('data').get('old').get('name')
    d['new'] = action.get('data').get('card') and action.get('data').get('card').get('name')
    d['closed'] = action.get('data').get('card') and action.get('data').get('card').get('closed')
    if not d.get('closed'):
        d['closed'] = False
    d['date'] = formatDateTime(action.get('date'))
    d['category'] = action.get('type')
    d['actor'] = action.get('memberCreator').get('fullName')
    return d

def flattenActions(actions):
    arr = []
    for action in actions:
        d = createActionDict(action)
        if d.get('after'):
            arr.append(d)
        else:
            #print(action.get('type'),action.get('before'))
            #print(action)
            # TBD: need to convert between list id and name for createCard
            pass
    return arr

def getListsForTargetBoard(client,desc):
    targetBoard = desc
    # Get Boards and find desc target
    boardId,boardName = client.getBoardByName(targetBoard)
    assert(boardId)
    #print("Found Trello Board. name='{}', id={}".format(boardName,boardId))
    # Get Lists on desc target Board
    boardLists = client.getLists(boardId)
    #print("Found Trello Lists for '{}' Board:".format(boardName))
    #for i,ls in enumerate(boardLists):
    #    print("{:02d}. name='{}', id={}".format(i,ls.get('name'),ls.get('id')))
    return boardName,boardId,boardLists

def procTrelloArguments(arguments):
    boardName = arguments.get('--b')
    assert(boardName)
    tcolors = []
    if arguments.get('--c'):
        tcolors = arguments.get('--c').split(',') 
    tlists = []
    if arguments.get('--l'):
        tlists = arguments.get('--l').split(',')
    output = None
    if arguments.get('--o'):
        output = arguments.get('--o')
    return boardName,tlists,tcolors,output

def main():
    import docopt
    usage="""

        %s - trelloBox
        --------------
        Usage:
        %s boards [-v]
        %s lists --b=<board> [-v]
        %s static --b=<board> [--c=<colors>] [--o=<output>] [-v] [-r] [-f]
        %s timed --b=<board> [--l=<lists>] [--c=<colors>] [--o=<output>] [-v] [-f]
        %s -h | --help
        %s -V | --version

        Options:
        -h --help               Show this screen.
        -v --verbose            Verbose mode.
        -V --version            Show version.
        -r --reverse            Reverse bars
        -f --force              Force data regeneration

        Examples:
        1. Get info on all Trello Boards:
        %s boards
        2.  Get info on all Lists in Trello Board 'My Board':
        %s lists --b="My Board"
        3. Create static visualisation of card counts for Lists in 'My Board' with given colors:
        %s static --b="My Board" --c="r,g,orange"
        4. Create time series visualistion of actions on all Lists in 'My Board' using default color palette:
        %s timed --b="My Board"
        5. Write time series visualistion of all actions in 'My Board' Lists using 'summer' color map to 'output.png':
        %s timed --b="My Board" --l="--c=summer --o="output.png"
        6. Create time series visualisations of actions on Lists P1,P2,New P in 'My Board' with given colors:
        %s timed --b="My Board" --l="P1,P2,New P" --c="r,g,b"

        """ % tuple([PROGRAM] * 13)

    arguments = docopt.docopt(usage)
    #print(arguments)
    verbose = False
    if arguments.get('--verbose') or arguments.get('-v'):
        verbose = True
    reverse = False
    if arguments.get('--reverse') or arguments.get('-r'):
        reverse = True
    force = False
    if arguments.get('--force') or arguments.get('-f'):
        force = True
    #initLogging(LOGFILE,VERBOSE)
    if arguments.get('--version') or arguments.get('-V'):
        print("%s version %s" % (PROGRAM,VERSION))
    elif arguments.get('--help') or arguments.get('-h'):
        print(usage)
    else:
        # Set up Trello client with our REST Handler
        try:
            rootUrl = 'https://api.trello.com/1'
            handler = RESTHandler(rootUrl)
            client = TrelloClient(handler,verbose)
            dp = TrelloDataProcessor(force)
        except:
            url = 'https://developers.trello.com/docs/api-introduction'
            print("Failed to set up Trello client")  
            print("Please check {} for how to set up Trello API credentials".format(url))
            sys.exit()
        if arguments.get('boards'):
            boards = client.getBoards()
            for brd in boards:
                id,name = brd.get('id'),brd.get('name')
                print("'{}' (id={})".format(name,id))
        elif arguments.get('lists'):
            boardName,tlists,tcolors,_ = procTrelloArguments(arguments)
            boardName,boardId,boardLists = getListsForTargetBoard(client,boardName)
            print("==== board='{}', id={} ====".format(boardId,boardName))
            for ls in boardLists:
                id,name = ls.get('id'),ls.get('name')
                print("'{}' (id={})".format(name,id))
        elif arguments.get('static'):
            boardName,lists,colors,output = procTrelloArguments(arguments)
            cards = dp.getCards()
            if force:
                print("Forcing data generation")
                # We have to go and pull and process all the data 
                boardName,_,boardLists = getListsForTargetBoard(client,boardName)
                # Get Cards on each target Board List
                cards = []
                for ls in boardLists:
                    id,name = ls.get('id'),ls.get('name')
                    listCards = client.getCardsByList(id)
                    for i,card in enumerate(listCards):
                        if len(name) > 13:
                            name = name[:13]
                        card['list'] = name
                        cards.append(card)
                        verbose and print("{:03d}. list='{}', name='{}', id={}".format(i,card.get('list'),card.get('name'),card.get('id')))
                    verbose and print("list='{}', listCards={}".format(card.get('list'),len(listCards)))
                print("{} Board cards found".format(len(cards)))
            else:
                print("Using 'cards.csv'")
            # Create a visualisation of the static card distribution by List 
            graph = dp.createCardDistributionBarChart(cards,camelCase(boardName),colors=colors,reverse=reverse,output=output)
            print("Generated static card distribution in '{}'".format(graph))
            #plt.show()
        elif arguments.get('timed'):
            boardName,selected,colors,output = procTrelloArguments(arguments)
            counts = dp.getCounts()
            start = dp.getStart()
            if force:
                print("Forcing data generation")
                boardName,_,boardLists = getListsForTargetBoard(client,boardName)
                # Get Actions on each List 
                cardIds = findUniqueCardIdsForActions(client.getActionsByList(boardLists))
                print("{} unique cards found".format(len(cardIds)))
                actions = flattenActions(client.getActionsByCard(cardIds))
                print("{} unique card actions found".format(len(actions)))
                # Find minimum date in actions array and use that for start. 
                dates = sorted([d.get('date') for d in actions])
                start = dates[0]
                dp.setStart(start)
                counts = dp.getActionCountsOverTime(actions,start)
            else:
                print("Using 'counts.csv'")
            # Create a visualisation of the time series distribution of Cards 
            graph = dp.createCardTimeSeriesStackedBarChart(counts,camelCase(boardName),selected,start,colors=colors,output=output)
            print("Generated time series distribution in '{}'".format(graph))
            #plt.show()

if __name__ == "__main__":
    main()
    sys.exit(0)