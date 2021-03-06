#!/usr/bin/env python

import os
import time
import re
from slackclient import SlackClient
import signal
import logging
from logging.handlers import RotatingFileHandler
import json
import requests
import random
from dotenv import load_dotenv

env_path = os.path.join('./', '.env')
load_dotenv(dotenv_path=env_path, verbose=True, override=True)

# Builds custom logger
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(filename)s : %(message)s'
    )
LOGFILE = "./slackbot.log"
r_logger = RotatingFileHandler(
    LOGFILE,
    mode='a',
    maxBytes=5*1024*1024,
    backupCount=2,
    encoding=None,
    delay=0)
r_logger.setFormatter(formatter)
logger.addHandler(r_logger)
logger.setLevel(logging.INFO)

# Constants
logged_in = True
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
DEFAULT = "-help"
starterbot_id = None


# This is just a test that shows you can raise your own exceptions
class CustomError(Exception):
    pass


def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals
    can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit
    it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """

    global logged_in
    if sig_num == signal.SIGINT:
        logger.warning(" SIGINT recieved from the os: program interrupted")
        logged_in = False
    elif sig_num == signal.SIGTERM:
        logger.warning(" SIGTERM recieved from the os: program terminated")
        logged_in = False


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to
        find bot commands. If a bot command is found, this function
        returns a tuple of command and channel. If its not found, then
        this function returns None, None.
    """
    for event in slack_events:
        # print json.dumps(event, sort_keys=True, indent=4)
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
        elif event["type"] == "hello":
            # Sends initial greeting to channel
            slack_client.api_call(
                "chat.postMessage",
                channel="#general",
                text="Here's Rover! (type: -help)"
            )
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning)
        in message text and returns the user ID which was mentioned.
        If there is no direct mention, returns None.
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username,
    # the second group contains remaining message
    return (
        matches.group(1),
        matches.group(2).strip()) if matches else (None, None)


def nasa_api():
    # # Connect to Nasa client
    nasa_site = (
        "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&page=2&api_key="  # noqa
        )
    nasa_token = os.getenv('NASA_API_KEY')
    mars_stuff = requests.get(nasa_site + nasa_token)
    result = json.loads(mars_stuff.content)
    photos_dict = result["photos"]
    photos_array = [pic['img_src'] for pic in photos_dict]
    return random.choice(photos_array)


def handle_command(command):
    """
        Interpret commands and send them to execute_command
    """
    response = None
    HELP = "-help"
    SUP = "sup?"
    NASA = "nasa"
    RAISE = "raise"
    SECRET_EXIT = "secret logout"

    # This is where you start to implement more commands!
    global logged_in
    if command.startswith(RAISE):
        raise CustomError("what the hell happened???")
    if command.startswith(HELP):
        response = "Try these commands: sup? / nasa"
    if command.startswith(SUP):
        response = "I'm a really boring and I only do one thing... say nasa"
    if command.startswith(NASA):
        response = nasa_api()
    if command.startswith(SECRET_EXIT):
        logged_in = False
        response = "Exiting..."
        logger.info("Connection terminated by user's exit command.")
    logger.info('User initiated command: {}'.format(command))
    return response


def execute_command(command, channel):
    """
        Executes bot command after handle_command runs
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(DEFAULT)
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=command or default_response
    )


def rtm_message_loop(slack_client):
    while logged_in:
        # This API call breaks the while loop if the test fails
        # so that the exception handler in "main" will catch error
        slack_client.api_call("api.test")
        # Runs commands if they are present
        try:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                cmd = handle_command(command)
                execute_command(cmd, channel)
        except CustomError as e:
            logger.info("something happened")
            logger.error(e)
        time.sleep(RTM_READ_DELAY)


if __name__ == "__main__":

    # Hook these two signals from the OS ..
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while logged_in:

        try:
            # Instantiate Slack client
            slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))

            if slack_client.rtm_connect(with_team_state=False):

                logger.info("Slackbot initialized!")

                # Read bot's user ID by calling Web API method `auth.test`
                starterbot_id = slack_client.api_call("auth.test")["user_id"]
                rtm_message_loop(slack_client)

            else:
                logger.error("Could not connect, will retry in 5 seconds...")
                time.sleep(5)

        except Exception as e:
            logger.error(e)
            logger.info("Connection error, will retry in 5 seconds")
            time.sleep(5)

    logger.error("Something happened and Rover stopped.")
