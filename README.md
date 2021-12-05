# Live football odds watcher

Multithreaded betting bot that compares live match statistics with live odds from your favourite bookmaker. It evaluates the current situation and sends notifications through Slack using the accompanying Slack connector.

Have this program observe all live football matches and notify you and your friends when there is a good betting opportunity!

### Slack notification example

<img src="./readme_assets/preview_w_border.png" alt="drawing" width="500"/>

<hr>

## How it works

The program fetches all upcoming matches each day. When a match goes live, a new thread is started with a "match observer" that compares live game statistics with live Asian Handicap odds (currently using Bet365) for that specific match. When a situation is evaluated to be good, notifications are sent to a slack channel to notify potential betters. The evaluation algorithm needs to be specified in **Game_observer.py**, I will not share mine. The application is currently set to Central Eastern Time, **CET** with support for **CEST** summer time. The Sportmonks Football API that is used has an incredible amount of information and this program can certainly be expanded for more thorough analyses, though I managed to make a working net positive ROI strategy only using Asian Handicaps.

## Prerequisites

- This project relies on having access to the [Sportmonks Football API](https://www.sportmonks.com/football-api/), and adding your account's *API Token* to **credentials.json**
- You need to create a [Slack app](https://api.slack.com/start/building), that will enable you to create messaging bots. See instructions below.

#### Creating the slack messaging bot
 - Create a new Slack workspace
 - Go to the [custom integrations panel](https://app.slack.com/apps/manage/custom-integrations), click **Bots**, and click **Add to Slack**
 - Choose a name for your bot, save the API integration token, and add this to the field 'slack_token' **credentials.json**
 - Create channels for *notifications* (required), *error* (optional), and *logs* (optional) and invite your bot to these channels by clicking **Details**, **More** and **Add App**
 - Add the names of your channels into their respective fields in **credentials.json**

Following these instructions, you should be good to go, and can invite any people to the notifications channel.


## Build and run instructions

- Modify the **credentials.json** file to include your slack connection token, sportmonks API token, and slack channel information
- Build the docker image by running ```docker build -t scanner_application .``` from the base directory
#### Deployment
The application is currently sharing the network with its host, be aware of any security implications this has.
- Start a new container on your local machine by running ```docker run --net=host -e TZ="Europe/Stockholm" scanner_application```
-  Or deploy the application to your favourite alternative Docker host. Here is a picture of mine!

![preview](./readme_assets/raspi.png)
