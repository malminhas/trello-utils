# trello-utils
This repo contains a number of utilities for extracting and visualising and reporting data in your Trello Boards:
* `trelloReporter.py`: inspects your Trello Boards and the Lists within them. It also allows you to visualise both a static view of current Card counts in any combination of those Lists and a time series stacked bar graph view built by tracking Card Actions over time.  The motivation for doing this is to allow a view on Card movement for issue tracking purposes in the scenario that Trello is being used as an issue tracking tool.  `trelloReporter.py` expects to find your Trello API Developer Key and App Token in two local files called `.ttrellokey` and `.ttrellotoken`.  For more instructions on how to obtain your developer credentials, check out the Trello support documentation [here](https://developers.trello.com/docs/api-introduction).  Note that the script leverages Trello API batch support to help stay under the Trello rate limit for API calls.
* `slackClient.py`: utility class for injecting either text or images into a Slack channel via Python `requests`
* `trelloClient.py`: utility class for interfacing to Trello Boards via Python `requests`
* `trelloDataProcessor.py`: utility class for preparing and graphing data gathered from Trello using Python `pandas`
* `googleDriveClient.py`: utility class for interfacing to Google Drive for documents via the Python `PyDrive` module

## Basic Examples
`trelloReporter.py` has an integrated command line which you can inspect as follows:
```
python trelloReporter.py -h
```
To list all your Trello Boards:
```
python trelloReporter.py boards
```
To enumerate all Lists within a Trello Board called `My Board`:
```
python trelloReporter.py lists --b="My Board"
```
To create a static horizontal bar graph visualisation of Card counts within all Lists in `My Board` with red|green|orange bars:
```
python trelloReporter.py static --b="My Board" --c="r,g,orange"
```
To create time series visualistion of actions on all Lists in 'My Board' using the default color palette:
```
python trelloReporter.py timed --b="My Board"
```
To write time series visualistion of all actions in 'My Board' Lists using 'summer' color map to file 'output.png':
```
python trelloReporter.py timed --b="Wand" --l="--c=summer --o="output.png"
```
To create time series visualisation of Actions on Lists `P1,P2,New P` in `My Board` using red|green|orange stacked bars:
```
python trelloReporter.py timed --b="My Board" --l="P1,P2,New P" --c="r,g,b"
```
To reverse the previous visualisation:
```
python trelloReporter.py timed -r --b="My Board" --l="P1,P2,New P" --c="b,g,r"
```

## Advanced Example: Slack Integration
A full example of working code showing how to integrate `trelloReporter.py` command line with Slack is below.  In order to get this to work, in addition to setting up your Trello credentials per the instruction above, you will also need to create a corresponding Slack application and save the corresponding token to a local file called `.slacktoken`.  This code will inject the generated graph into a Slack channel called `#reporting`.  To fully automate you could integrate this script into Jenkins or set up an AWS Lambda function.

```
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
			c = 'python trelloReporter.py static'
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
```

## Installation
Install all dependencies using pip as follows:
```
pip install -r requirements.txt
```
For Slack support you will need to create a corresponding Slack application and save the corresponding token to a local file called `.slacktoken`.
You will also need to set up a Trello Developer API Key and an API Token per the instructions outlined on the Trello Developers site [here](https://developers.trello.com/docs/api-introduction).

## Outstanding
* Add more support to `trelloReporter.py` command line for basic Trello functionality.
* Consider leveraging comprehensive [py-trello](https://github.com/sarumont/py-trello) for that basic functionality.
* Look at analysing the contents of Cards in more detail.

## Licence 
[Apache Licence 2.0](http://www.apache.org/licenses/LICENSE-2.0)
