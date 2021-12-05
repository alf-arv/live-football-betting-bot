import slack
from Slack_connector import Slack_message_bot
from Game_observer import Observer
from datetime import datetime as dt
from datetime import timedelta
import requests
import json
import time
import _thread

def import_credentials():
    """
    Import credentials and tokens for api and slack connectivity

    @return: slack token, notifications, errors and logs channels & sportmonks api token
    """

    data = json.load(open('credentials.json',))

    # allow for errors channel not to be specified
    try:
        errors_channel = data['slack_errors_channel']
    except:
        errors_channel = None

    # allow for logs channel not to be specified
    try:
        application_logs_channel = data['application_logs_channel']
    except:
        application_logs_channel = None

    return data['slack_token'], data['slack_notifications_channel'], errors_channel, application_logs_channel, data['sportmonks_api_token']


def currently_active_game():
    """
    Check if there is a currently active game

    @return: id of active game
    """

    if upcoming_games:
        next_game = upcoming_games[0]
    else:
        next_game = [dt.now()+timedelta(weeks=100)]
    # Get current time
    time_now = str(dt.now().time())[:-10] # gives string ex: '14:55'
    time_now = dt.strptime(time_now,'%H:%M')

    # If a game in upcoming_games has started, return its ID
    if next_game[0] <= time_now:
        # Remove first element of games list
        upcoming_games.pop(0)

        # Return the game ID
        return next_game[1]

    # Option: Run past games that are still running
    if len(past_games) > 0:
        if past_games[-1][0] >= time_now-timedelta(minutes=80):
            print(f"A past game is still running, returning its id {past_games[-1][1]}")
            temp = str(past_games[-1][1])
            past_games.pop(-1)
            return temp

    # Else return Null
    return None


def new_game_observer(game_id, api_token, notifications_channel, errors_channel, slack_token):
    """
    Procedure for safely starting up a new game observer

    @return: -1 when done
    """

    # Instantiate observer
    o = Observer(game_id, api_token, notifications_channel, errors_channel, slack_token)

    # Assert connection is working
    if not o.connection_working():
        raise Exception("Connection to sportmonks API is not working")

    # Wait for API to confirm game is live
    game_started = o.wait_for_game_to_start()
    if not game_started:
        return -1

    # Start observing game
    o.observe()

    # Terminate
    print("Game observer closes")
    return -1


def fetch_upcoming_games(api_token, summertime):
    """
    Fetch upcoming games from API and stores upcoming and past games in their
    respective lists upcoming_games and past_games.

    @return: None
    """
    global upcoming_games, past_games

    upcoming_games = []
    past_games = []

    # Fetch the upcoming games
    raw_response = requests.get(url=f"https://soccer.sportmonks.com/api/v2.0/fixtures/date/{dt.now().date()}", params={"api_token": api_token, "tz": "CET"})
    response = raw_response.json()

    try:
        data = response['data']
    except:
        raise Exception("The sportmonks response did not contain any data, double check your account subscription status and the information provided in credentials.json")

    # Save current time
    time_now = str(dt.now().time())[:-10] # gives string ex: '14:55'
    time_now = dt.strptime(time_now,'%H:%M')

    # Add all upcoming matches to upcoming_games
    for i in data:
        id = i["id"]
        time = i["time"]["starting_at"]["time"]
        time = dt.strptime(time,'%H:%M:%S')
        if summertime:
            time = time + timedelta(hours=1) # adjust starttimes for summertime
        if not( (time_now-time).days > -1 ): # if starttime is ahead of us
            upcoming_games.append((time, id)) # appending (time, id)
        else:
            past_games.append((time, id))

    # Sort the list
    upcoming_games.sort()

    # Print past and upcoming games
    print(f'Past games today:\n {list(map(lambda g: "game %s at %s"%(str(g[1]), str(g[0].time())), past_games))}\n')
    print(f'Upcoming games:\n {list(map(lambda g: "game %s at %s"%(str(g[1]), str(g[0].time())), upcoming_games))}\n')

    return upcoming_games


def main():
    # Import credentials
    token, notifications_channel, errors_channel, logs_channel, sportmonks_token = import_credentials()

    # Create logger and establish its connection
    application_logger = Slack_message_bot(token, logs_channel)
    application_logger.connect()

    # Save the current timestamp
    current_day = dt.now()

    # Fetch upcoming games today
    fetch_upcoming_games(sportmonks_token, True) # CURRENTLY: summertime == True

    # Notify application started
    application_logger.post_message('Application started')

    # Event loop
    while True:
        active_game = currently_active_game()
        if active_game:
            print("Starting thread with new observer")
            try:
                _thread.start_new_thread(new_game_observer, (active_game, sportmonks_token, notifications_channel, errors_channel, token))
                application_logger.post_message(f"*{active_game}:* Observer started")
            except:
                application_logger.post_message(f"*{active_game} Exception:* The thread for this observer could not start")
        time.sleep(120)

        # If a new day begins: fetch upcoming games & refresh the current_day
        if (current_day.day - dt.now().day == -1):
            current_day = dt.now()
            upcoming = fetch_upcoming_games(sportmonks_token, True)
            application_logger.post_message(f'*Upcoming games {str(current_day)[:10]}:* {str(list(map(lambda g: "game %s at %s"%(str(g[1]), str(g[0].time())), upcoming_games)))}')

if __name__ == "__main__":
    main()
