import slack

class Slack_message_bot:

    def __init__(self, token, channel):
        """
        Constructor

        token: String of slack API token for authentication
        channel: The name of the channel in which to post messages
        """
        self.TOKEN = token
        self.CHANNEL = channel

    def connect(self):
        """
        Establishes a connection to the slack client using self.token
        Does nothing if channel is Null

        @return: True if successful, False otherwise
        """
        if self.CHANNEL == None:
            return True

        try:
            self.connection = slack.WebClient(token=self.TOKEN)
        except:
            raise Exception("Connection to Slack could not be established, verify the provided slack token")
        return True

    def post_message(self, message):
        """
        Posts message to the channel self.channel
        Does nothing if channel is Null

        message: String object of message to post

        @return: True if successful post
        """

        if self.CHANNEL == None:
            return True

        try:
            self.connection.chat_postMessage(
                channel=self.CHANNEL,
                text = message)
        except:
            raise Exception("Message could not be posted, verify that the provided channel exists")
        return True
