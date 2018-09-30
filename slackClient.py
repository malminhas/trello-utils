#!/usr/bin/env python
#
# slackClient.py
# --------------
#
# Mal Minhas <mal@kano.me>
# Copyright (c) 2018 Kano Computing. All Rights Reserved.
# Licence: GPLv3
#
# Installation:
# --------------
# You will need to create a Slack App first.
# You will need a one time OAuth flow to get hold of your Slack token: 
# https://slackapi.github.io/python-slackclient/auth.html#handling-tokens-and-other-sensitive-data
# You can retrieve the token for your app from OAuth&Permissions link
# https://api.slack.com/apps/ACW8VFRB3/oauth?'
# Incoming webhook: 
# https://hooks.slack.com/services/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
#

SLACK_TOKEN_FILE 	= '.slacktoken'

class SlackClient(object):
	def __init__(self):
		self.token = self.getToken(SLACK_TOKEN_FILE,'slack')

	def getToken(self,tokenFile,credType):
		if os.path.exists(tokenFile):
			with open(tokenFile,'r') as f:
				self.token = f.read()
				assert(len(token))
		else:
			token = getpass.getpass('{} token:'.format(credType))
			with open(tokenFile,'w') as f:
				f.write(token)
		return token

	def post_text(self,text, token, channels):
		responses = []
		for channel in channels:
			response = requests.post(url='https://slack.com/api/chat.postMessage', data=
				{'token': token, 'channel': channel, 'text': text}, 
				headers={'Accept': 'application/json'})
			responses.append(response.text)
		return responses

	def post_image(self,filename, token, channels):
		''' Using token '''
		responses = []
		f = {'file': (filename, open(filename, 'rb'), 'image/png', {'Expires':'0'})}
		for channel in channels:
			response = requests.post(url='https://slack.com/api/files.upload', data=
				{'token': token, 'channels': channel, 'media': f}, 
				headers={'Accept': 'application/json'}, files=f)
			responses.append(response.text)
		return responses


