# trello-utils
This repo contains tools for extracting and visualising data in your Trello Boards.:
* `trelloMetrics.py` allows you to enumerate your Trello Boards and the Lists within them. It also allows you to visualise both a static view of current Card counts in each List and a time series stacked bar graph view built by tracking Card Actions over time.  The motivation for doing this is to allow a view on Card movement for issue tracking purposes in the scenario that Trello is being used as an issue tracking tool.

## Examples
`trelloMetrics.py` has an integrated command line which you can inspect as follows:
```
python trelloMetrics.py -h
```
To list all your Trello Boards:
```
python trelloMetrics.py boards
```
To enumerate all Lists within a Trello Board called `My Board`:
```
python trelloMetrics.py lists --b="My Board"
```
To create a static horizontal bar graph visualisation of Card counts within all Lists in `My Board` with red|green|orange bars:
```
python trelloMetrics.py static --b="My Board" --c="r,g,orange"
```
To create time series visualistion of actions on all Lists in 'My Board' using the default color palette:
```
python trelloMetrics.py timed --b="My Board"
```
To create time series visualisation of Actions on Lists `P1,P2,New P` in `My Board` using red|green|orange stacked bars:
```
python trelloMetrics.py timed --b="My Board" --l="P1,P2,New P" --c="r,g,b"
```
To reverse the previous visualisation:
```
python trelloMetrics.py timed -r --b="My Board" --c="g,g,g,g,g,g,g,g,g,y,r,b,b,b,b"
```

## Installation
Install all dependencies using pip as follows:
```
pip install -r requirements.txt
```
You will also need to set up a Trello Developer API Key and an API Token per the instructions outlined on the Trello Developers site [here](https://developers.trello.com/docs/api-introduction). 

## Outstanding
* Add more support to `trelloMetrics.py` command line for basic Trello functionality.
* Look at analysing the contents of Cards in more detail.

## Licence 
[Apache Licence 2.0](http://www.apache.org/licenses/LICENSE-2.0)
