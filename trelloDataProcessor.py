#!/usr/bin/env python
#
# trelloDataProcessor.py
# ----------------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import cm
import seaborn as sns
# use Seaborn styles
sns.set()
import os
import arrow
import datetime

formatDateTime = lambda s: arrow.get(s).format('YYYY-MM-DD HH:mm:ss')

class TrelloDataProcessor(object):
    def __init__(self,force,verbose=False):
        self.verbose = verbose
        self.force = force
        self.start = None
        self.cards = pd.DataFrame()
        self.counts = pd.DataFrame()
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
        if not colors:
            colors.append('cool') # default
        if colors[0] in ['summer','autumn','winter','spring','cool']:
            cmap = cm.get_cmap(colors[0])
            colors = None
        if df.shape[0] > 50:
            print('Greater than 50 date values!')
            # More than 50 dates to plot => need to switch to default xaxis handling
            if colors:
                ax = df[selected].plot(kind='bar',stacked=True,color=colors,xticks=df.index,
                    title='{} Board time series {}'.format(desc,today),figsize=(24,12))
            else:
                ax = df[selected].plot(kind='bar',stacked=True,cmap=cmap,xticks=df.index,
                    title='{} Board time series {}'.format(desc,today),figsize=(24,12))                    
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
        plt.subplots_adjust(top=0.8) # Provides margin at bottom to accommodate legend
        plt.subplots_adjust(bottom=0.2) # Provides margin at bottom to accommodate axis
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
