#!/usr/bin/env python
#
# trelloReporter.py
# -----------------
# Script to generate metrics data from Trello Boards.
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#
# Installation:
# ------------
# $ pip install -r requirements.txt
#

import sys
from trelloClient import TrelloClient
from trelloRestHandler import TrelloRESTHandler
from trelloDataProcessor import TrelloDataProcessor,formatDateTime

PROGRAM             = __file__
VERSION             = '0.5'

camelCase = lambda s: ''.join(x for x in s.title() if not x.isspace())

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
    '''
    Returns: boardName,boardId,list of dict of boardList entries
    '''
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

def generateCards(client,boardName,verbose):
    '''
    Returns: list of dict of card data (list,name,id)
    '''
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
    verbose and print("{} Board cards found".format(len(cards)))
    return cards

def generateCardCounts(client,dp,boardName,verbose):
    boardName,_,boardLists = getListsForTargetBoard(client,boardName)
    # Get Actions on each List 
    cardIds = findUniqueCardIdsForActions(client.getActionsByList(boardLists))
    verbose and print("{} unique cards found".format(len(cardIds)))
    actions = flattenActions(client.getActionsByCard(cardIds))
    verbose and print("{} unique card actions found".format(len(actions)))
    # Find minimum date in actions array and use that for start. 
    dates = sorted([d.get('date') for d in actions])
    start = dates[0]
    dp.setStart(start)
    counts = dp.getActionCountsOverTime(actions,start)
    return counts

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

def dumpBoards(boards):
    for brd in boards:
        id,name = brd.get('id'),brd.get('name')
        print("'{}' (id={})".format(name,id))

def dumpBoardLists(boardName,boardId,boardLists):
    print("==== board='{}', id={} {} lists ====".format(boardName,boardId,len(boardLists)))
    for ls in boardLists:
        id,name = ls.get('id'),ls.get('name')
        print("'{}' (id={})".format(name,id))

def findTargetInBoardLists(target,boardLists):
    for ls in boardLists:
        if ls.get('name') == target:
            return ls
    return None

def createSummary(client,boardLists,tlists):
    '''
    Receives: list of boardList names, list of dict of boardList entries
    Returns: summary string
    '''
    s = ''
    boardListNames = [b.get('name') for b in boardLists]
    for target in tlists:
        ls = findTargetInBoardLists(target,boardLists)
        if ls:
            id,listname = ls.get('id'),ls.get('name')
            listCards = client.getCardsByList(id)
            for i,card in enumerate(listCards):
                name = card.get('name')
                url = card.get('shortUrl')
                def procLabel(name,color):
                    if name in ['bug']:
                        return ':{}:'.format(name)
                    elif name in ['world']:
                        return ':globe_spin:'
                    elif color in ['red','blue']:
                        return ':{}_circle:'.format(color)
                    return name
                labels = ' '.join(sorted([procLabel(l.get('name').lower(),l.get('color').lower()) for l in card.get('labels')]))
                s += "{}-{:02d}. `{}` {} labels={}\n".format(listname,i+1,name,url,labels)
    return s

def main():
    import docopt
    usage="""

        %s
        --------------
        Usage:
        %s boards [-v]
        %s lists --b=<board> [-v]
        %s summary --b=<board> --l=<lists> [-v]
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
        3.  Get Card titles for Lists P2 and P3 in Trello Board 'My Board':
        %s summary --b="My Board" --l="P1,P2"
        4. Create static visualisation of card counts for Lists in 'My Board' with given colors:
        %s static --b="My Board" --c="r,g,orange"
        5. Create time series visualistion of actions on all Lists in 'My Board' using default color palette:
        %s timed --b="My Board"
        6. Write time series visualistion of all actions in 'My Board' Lists using 'summer' color map to 'output.png':
        %s timed --b="My Board" --l="P1,P2,New P"--c=summer --o="output.png"
        7. Create time series visualisations of actions on Lists P1,P2,New P in 'My Board' with given colors:
        %s timed --b="My Board" --l="P1,P2,New P" --c="r,g,b"
        """ % tuple([PROGRAM] * 15)

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
            handler = TrelloRESTHandler(rootUrl)
            client = TrelloClient(handler,verbose)
            dp = TrelloDataProcessor(force)
        except Exception as e:
            print(e)
            url = 'https://developers.trello.com/docs/api-introduction'
            print("Failed to set up Trello client")  
            print("Please check {} for how to set up Trello API credentials".format(url))
            sys.exit()
        if arguments.get('boards'):
            boards = client.getBoards()
            dumpBoards(boards)
        elif arguments.get('lists'):
            boardName,tlists,tcolors,_ = procTrelloArguments(arguments)
            boardName,boardId,boardLists = getListsForTargetBoard(client,boardName)
            dumpBoardLists(boardName,boardId,boardLists)
        elif arguments.get('summary'):
            boardName,tlists,_,_ = procTrelloArguments(arguments)
            boardName,boardId,boardLists = getListsForTargetBoard(client,boardName)
            listSummary = createSummary(client,boardLists,tlists)
            print(listSummary)
        elif arguments.get('static'):
            boardName,lists,colors,output = procTrelloArguments(arguments)
            print(lists)
            print(colors)
            cards = dp.getCards()
            if force or cards.empty:
                print("Forcing new cards data generation")
                cards = generateCards(client,boardName,verbose)
            else:
                print("Using existing 'cards.csv'")
            # Create a visualisation of the static card distribution by List 
            graph = dp.createCardDistributionBarChart(cards,camelCase(boardName),colors=colors,reverse=reverse,output=output)
            print("Generated static card distribution in '{}'".format(graph))
            #plt.show()
        elif arguments.get('timed'):
            boardName,selected,colors,output = procTrelloArguments(arguments)
            counts = dp.getCounts()
            start = dp.getStart()
            if force or counts.empty:
                print("Forcing new card counts data generation")
                counts = generateCardCounts(client,dp,boardName,verbose)
            else:
                print("Using existing 'counts.csv'")
            # Create a visualisation of the time series distribution of Cards 
            graph = dp.createCardTimeSeriesStackedBarChart(counts,camelCase(boardName),selected,start,colors=colors,output=output)
            print("Generated time series distribution in '{}'".format(graph))
            #plt.show()

if __name__ == "__main__":
    main()
    sys.exit(0)