#!/usr/bin/env python

import os 
import time
import re 
from slackclient import SlackClient
import signal
import logging
import json

env_path = os.path.join('./', '.env')
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, verbose=True, override=True)

# Builds custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(filename)s:%(message)s')
file_handler = logging.FileHandler('slackbot.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# constants
logged_in = True
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
DEFAULT = "-help"
HELP = "-help"
BEETS = "beets?"
EGGS = "eggs?"
EXIT = "exit"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


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
        logger.info(" SIGINT recieved from the os: program terminated w/ ctr-c")
        logged_in = False
    elif sig_num == signal.SIGTERM:
        logger.info(" SIGTERM recieved from the os: program terminated")
        logged_in = False


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        # print json.dumps(event, sort_keys=True, indent=4)  
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
        elif event["type"] == "hello":
            # Sends initial greeting to channel
            slack_client.api_call(
                "chat.postMessage",
                channel="CCRPND1V4",
                text="Here's Bobby! (type: -help)"
            )
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command):
    """
        Interpret commands and send them to 
    """
    response = None
    # This is where you start to implement more commands!
    global logged_in
    if command.startswith(HELP):
        response = """Try these commands: beets? / eggs? / exit"""
    if command.startswith(BEETS):
        response = "I like 'em."
    if command.startswith(EGGS):
        response = "I like those too..."
    if command.startswith(EXIT):
        logged_in = False
        response = "Exiting..."
        print("Connection failed. Exception traceback printed above.")
        logger.info('Slackbot terminated.')
    return response


def execute_command(command, channel):
    """
        Executes bot command
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(DEFAULT)
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=command or default_response
    )
    
if __name__ == "__main__":

    # Hook these two signals from the OS ..
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Prints to log when program has started
    logger.info('Slackbot initialized!')

    # instantiate Slack client
    slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))
    # starterbot's user ID in Slack: value is assigned after the bot starts up
    starterbot_id = None

    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while logged_in:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                cmd = handle_command(command)
                execute_command(cmd, channel)

            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")