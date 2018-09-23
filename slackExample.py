import subprocess
import os, requests
import arrow

def getToken(tokenFile,credType):
	if os.path.exists(tokenFile):
		with open(tokenFile,'r') as f:
			token = f.read()
			assert(len(token))
	else:
		token = getpass.getpass('{} token:'.format(credType))
		with open(tokenFile,'w') as f:
			f.write(token)
	return token

def post_text(text, token, channel):
	response = requests.post(url='https://slack.com/api/chat.postMessage', data=
		{'token': token, 'channel': channel, 'text': text}, 
		headers={'Accept': 'application/json'})
	return response.text

def post_image(filename, token, channels):
	''' Using token '''
	f = {'file': (filename, open(filename, 'rb'), 'image/png', {'Expires':'0'})}
	response = requests.post(url='https://slack.com/api/files.upload', data=
		{'token': token, 'channels': channels, 'media': f}, 
		headers={'Accept': 'application/json'}, files=f)
	return response.text

def createStaticVisualisation(date,board,force=False,toSlack=False,channel=''):
	try:
		o = "Example_{}.png".format(date)
		if force:
			c = 'python trelloMetrics.py static'
			cl = '{} -r --b="{}" --c="g,y,pink,r,r,r,r,r" --o="{}" --force'.format(c,board,o)
		else:
			cl = '{} -r --b="{}" --c="g,y,pink,r,r,r,r,r" --o="{}"'.format(c,board,o)
		r = subprocess.check_output(cl, shell=True,stderr=subprocess.STDOUT)
		blurb = "Distribution of cards in {} {}".format(board,date)
		if toSlack:
			print(post_text(text=blurb, token=token, channel =channel))
			print(post_image(filename=o, token=token, channels =channel))
		else:
			print("Not pushing {} to Slack".format(o))
	except subprocess.CalledProcessError as e:
		raise RuntimeError("command '{}' return with error (code {}): {}".\
		  format(e.cmd, e.returncode, e.output))

if __name__ == '__main__':
	force = True
	toSlack = False
	board = 'MyBoard'
	ch = '#reporting'
	token = getToken('.slacktoken','slack')
	today = arrow.utcnow().format("DD-MM-YYYY")
	createStaticVisualisation(today,board,force=force,toSlack=toSlack,channel=ch)
