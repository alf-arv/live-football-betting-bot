from datetime import datetime, timedelta
from requests import get
import requests
import time
from Slack_connector import Slack_message_bot

class Observer:

    def __init__(self, game_id, api_token, slack_notifications_channel, slack_errors_channel, slack_token):
        self.game_id = game_id
        self.timezone = "CEST"
        self.api_token = api_token
        self.localteam_info = None
        self.visitorteam_info = None
        self.localteam_id = None
        self.visitorteam_id = None
        self.slacktoken = slack_token
        self.notifications_channel = slack_notifications_channel
        self.errors_channel = slack_errors_channel


    def connection_working(self):
        """
        Establishes a connection to the sportmonks API
        using the credentials & tokens in credentials.json

        @return: True if successful
        """

        try:
            # test request to see if any answer arrives
            raw_response = requests.get(url="https://soccer.sportmonks.com/api/v2.0/livescores/now", params={"api_token": self.api_token})
        except:
            raise Exception("Connection could not be established, URL likely wrong")

        try:# TODO: change this to something more elegant
            if raw_response.json()["error"]:
                raise Exception("Error recieved from API, auth token likely wrong")
        except:
            print("token accepted by API")

        return True


    def game_is_live(self):
        """
        Check if game is live by requesting the fixture's time status

        @return: True if game is live, False otherwise
        """

        try:
            raw_response = requests.get(url=f"https://soccer.sportmonks.com/api/v2.0/fixtures/{self.game_id}", params={"api_token": self.api_token})
        except:
            raise Exception("Connection could not be established, game_id likely incorrect")

        response = raw_response.json()
        if response["data"]["time"]["status"]:
            if response["data"]["time"]["status"] == "LIVE" or response["data"]["time"]["status"] == "HT":
                return True
        return False


    def wait_for_game_to_start(self):
        """
        Wait for maximum of 15 minutes for game to be reported as LIVE from sportmonks.
        This is a precaution to avoid errors caused by delays.

        @return: True when game is live, False otherwise
        """

        print(f"Waiting for game {self.game_id} to start")
        for i in range(45):
            if self.game_is_live():
                print(f"{self.game_id} is now reported to be live, continues...")
                return True
            time.sleep(20)

        error_notificator.post_message(f'*{self.game_id}:* Game never reported to be live in its first 15 mins, thread terminating')
        return False


    def fetch_team_from_id(self, team_id):
        """
        Fetches the name and country of team id passed as argument

        @return: team name, country
        """

        try:
            # test request to see if any answer arrives
            raw_response = requests.get(url=f"https://soccer.sportmonks.com/api/v2.0/teams/{team_id}", params={"api_token": self.api_token, "include":"country", "tz":str(self.timezone)})
        except:
            error_notificator.post_message(f'*{self.game_id} Exception:* Connection to soccer API could not be established')
            raise Exception("Connection could not be established, URL likely wrong")
        response = raw_response.json()

        # Return teamname, country
        return response["data"]["name"], response["data"]["country"]["data"]["name"]


    def fetch_current_data(self):
        """
        Fetches all relevant match data using requests, and builds a
        dictionary object suitable for evaluation/comparison

        @return: dictionary of the match data
        """

        # Get livescores
        params = {"api_token": self.api_token, "tz": str(self.timezone), "include": "stats"}
        raw_response = requests.get(url="https://soccer.sportmonks.com/api/v2.0/livescores/now", params=params)
        response = raw_response.json()
        if "error" in response:
            error_notificator.post_message(f'*{self.game_id} Exception:* {response["error"]["message"]}')
            raise Exception(response["error"]["message"])

        # Filter out irrelevant matches
        correct_match = None
        for i in response['data']:
            if str(i['id']) == str(self.game_id):
                correct_match = i
                break

        # Throw error if this observer's match cant be found
        if not correct_match:
            error_notificator.post_message(f"*{self.game_id} Exception:* Correct match could not be found in [...]/livescores/now ")
            raise Exception(f"Correct match could not be found in [...]/livescores/now for match {self.game_id}")

        # If not already saved, save the team names and countries
        if not self.localteam_info:
            self.localteam_id = correct_match["localteam_id"]
            self.visitorteam_id = correct_match["visitorteam_id"]
            self.localteam_info = self.fetch_team_from_id(str(self.localteam_id))
            self.visitorteam_info = self.fetch_team_from_id(str(self.visitorteam_id))

        # Save stats for the local team and visitor team
        stats = {}
        if correct_match['stats']['data'][0]["team_id"] == self.localteam_id:
            stats['localteam'] = correct_match['stats']['data'][0]
            stats['visitorteam'] = correct_match['stats']['data'][1]
        elif correct_match['stats']['data'][0]["team_id"] == self.visitorteam_id:
            stats['visitorteam'] = correct_match['stats']['data'][0]
            stats['localteam'] = correct_match['stats']['data'][1]

        # If information is not complete, return dummy dict temporarily
        try:
            if (len(stats) == 0) or (stats['localteam']['shots'] == None) or (stats['visitorteam']['shots'] == None) or (stats['localteam']['attacks'] == None) or (stats['visitorteam']['attacks'] == None) or (stats['localteam']['possessiontime'] == None) or (stats['visitorteam']['possessiontime'] == None):
                print('Some stats are None, sleeping and returning dummy object full of 0s...')
                return {'localteam': {'shots':{'ongoal':0, 'offgoal':0}, 'attacks':{'dangerous_attacks':0, 'attacks':0}, 'possessiontime':0},'visitorteam':{'shots':{'ongoal':0, 'offgoal':0}, 'attacks':{'dangerous_attacks':0, 'attacks':0}, 'possessiontime':0}}
        except:
            return {'localteam': {'shots':{'ongoal':0, 'offgoal':0}, 'attacks':{'dangerous_attacks':0, 'attacks':0}, 'possessiontime':0},'visitorteam':{'shots':{'ongoal':0, 'offgoal':0}, 'attacks':{'dangerous_attacks':0, 'attacks':0}, 'possessiontime':0}}

        return stats


    def fetch_current_odds(self):
        """
        Fetches the relevant odds for evaluate_situation() to be able to do its job

        @return: list of odds dictionarys
        """

        # Request all odds of inplay matches
        params = {"api_token": self.api_token, "tz":str(self.timezone)}
        raw_response = requests.get(url=f"https://soccer.sportmonks.com/api/v2.0/odds/inplay/fixture/{self.game_id}", params=params)
        response = raw_response.json()

        # Filter out other odd types
        asian_handicap_object = None
        for i in response['data']:
            if "asian handicap" in str(i['name']).lower() and not "half" in str(i['name']).lower():
                asian_handicap_object = i
                break

        # Crash if asian handicaps can't be found
        if not asian_handicap_object:
            error_notificator.post_message(f"*{self.game_id} Exception:* No asian handicap odds can be found for match {self.game_id}")
            raise Exception(f"No asian handicap odds can be found for match {self.game_id}")

        # Filter out other bookmakers
        b365_asian_odds_object = None
        for i in asian_handicap_object['bookmaker']['data']:
            if str(i['name']) == "bet365":
                b365_asian_odds_object = i
                break

        # Crash if odds can't be found
        if not b365_asian_odds_object:
            error_notificator.post_message(f"*{self.game_id} Exception:* No bet information could be found originating from bet365 for match {self.game_id}")
            raise Exception(f"No bet information could be found originating from bet365 for match {self.game_id}")

        # Extract list of odds dictionaries
        list_of_odds = b365_asian_odds_object['odds']['data']

        return list_of_odds


    def evaluate_situation(self, stats, odds):
        """
        Do comparisons and evaluations of the stats.
        If the odds are good enough then notify the  slack channel.

        Fill this function with your evaluation criteria, I don't want to reveal my strategy

        stats: dictionary containing the stats for 'localteam' and 'visitorteam'
        odds: list of odds objects

        @return: dictionary of the evaluation results
        """

        """
        Examples:
        stats['localteam'] looks like this:
                {
                    "team_id": 314,
                    "fixture_id": 11853602,
                    "shots": {
                        "total": 11,
                        "ongoal": 4,
                        "offgoal": 7,
                        "blocked": null,
                        "insidebox": null,
                        "outsidebox": null
                    },
                    "passes": null,
                    "attacks": {
                        "attacks": 80,
                        "dangerous_attacks": 50
                    },
                    "fouls": null,
                    "corners": 5,
                    "offsides": null,
                    "possessiontime": 49,
                    "yellowcards": 3,
                    "redcards": 0,
                    "yellowredcards": null,
                    "saves": null,
                    "substitutions": 3,
                    "goal_kick": null,
                    "goal_attempts": null,
                    "free_kick": null,
                    "throw_in": null,
                    "ball_safe": null,
                    "goals": null,
                    "penalties": null,
                    "injuries": null,
                    "tackles": null
                }


        the asian handicap odds-objects in the list 'odds' look like this:
                {
                  "label": "1",
                  "value": "1.98",
                  "extra": null,
                  "probability": "50.51%",
                  "dp3": "1.980",
                  "american": -103,
                  "factional": null,
                  "handicap": "-3.0",
                  "total": null,
                  "winning": true,
                  "stop": false,
                  "bookmaker_event_id": 91152453,
                  "last_update": {
                    "date": "2020-08-02 15:28:10.103929",
                    "timezone_type": 3,
                    "timezone": "UTC"
                  }
                }
        """

        """
        Return decision

        Example: {"bet": True, "onTeam": "Team name", "odds": [1.98, 2.59]}
        """
        return None


    def observe(self):
        """
        Observes the game specified by self.game_id, evaluating stats,
        sending notifications on Slack if a bet should be placed
        """
        global error_notificator

        # Create messaging bots and establish their connections
        notificator = Slack_message_bot(self.slacktoken, self.notifications_channel)
        notificator.connect()
        error_notificator = Slack_message_bot(self.slacktoken, self.errors_channel)
        error_notificator.connect()

        # calculate time to stop observing
        match_ends = datetime.now() + timedelta(minutes=90)
        muted_until = datetime.now()

        # Sleep for 10 minutes
        for i in range(10):
            time.sleep(60)

        # Event loop
        while datetime.now() < match_ends:
            time.sleep(30)
            # Iff not muted...
            if (datetime.now() - muted_until).days == 0:
                # ... evaluate the situation ...
                result = self.evaluate_situation(self.fetch_current_data(), self.fetch_current_odds())
                # ... and if a bet should be placed; post in slack and update mute timestamp
                if result["bet"]:
                    notificator.post_message(f'A bet should be placed now, on *{result["onTeam"]}*, {self.fetch_team_from_id(result["onTeam"])} on one of these good bets: *{result["odds"]}*')
                    muted_until = datetime.now()+timedelta(minutes=15)

        print(f"Match {self.game_id} ended")
