#!/usr/bin/env python3
from lib import *
from modules import *

from cpuinfo import get_cpu_info
from io import StringIO
from threading import Thread

import base64
import datetime
import distro
import functools
import json
import logging
import os
import pendulum
import platform
import psutil
import praw
import re
import requests
import schedule
import shlex
import slackclient
import time
import threading
import websocket
import zlib

UPTIME = datetime.datetime.now()

log_stream = StringIO()
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(stream=log_stream)
    ])

with open('config.json', 'r') as f:
	config = json.load(f)

slack_client = slackclient.SlackClient(config['slack_token'])
bot_id = None

# Slack Constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def get_config():
	return config

def get_id(id):
	return id.split('_')[1]

def format_removal_reply(reason, author, permalink, kind):
	if kind == 'submission':
		reply = config['removals']['header'] + "\n\n" + reason + "\n\n" + config['removals']['footer']
	elif kind == 'comment':
		reply = config['removals']['comment_header'] + "\n\n" + reason + "\n\n" + config['removals']['comment_footer']
	reply = reply.replace("{author}", str(author))
	reply = reply.replace("{kind}", kind)
	reply = reply.replace("{subreddit}", config['subreddit'])
	reply = reply.replace("{url}", permalink)
	return reply

def reply(channel, response):
	return slack_client.api_call("chat.postMessage", channel=channel, text=response)

def update(channel, response, ts):
	return slack_client.api_call("chat.update", channel=channel, text=response, ts=ts)

def log(level, msg):
	try:
		clevel = config['logging']['level']
	except:
		return

	if level == "info":
		logging.info(msg)
	elif level == "warn":
		logging.warning(msg)
	elif level == "exception":
		logging.exception(msg)

	logging.exception('\n')

	try:
		line = log_stream.getvalue().splitlines()[-1]
	except IndexError:
		return

	if (level == "info" and clevel == "info") or (level == "warn" and (clevel == "warn" or clevel == "info")) or (level == "exception" and clevel):
		print(line)

		if config['logging']['channel']:
			reply(config['logging']['channel'], line)

		if config['logging']['file']:
			with open(config['logging']['file'], 'a+') as f:
				f.write(line + '\n')

def get_args(message_text):
	args = {}
	message_text = message_text[len(message_text.split()[0]):].replace('“','"').replace('”','"')
	regex = re.compile(r"(?P<key>[^\s]*?)=(?P<value>(?:(?!([^\s]*?)=).)*)", re.DOTALL)
	for (k, v, e) in re.findall(regex, message_text):
		v = v.strip()
		if v.startswith('"') and v.endswith('"'):
			v = v[1:-1]
		args[k] = v

	return args

def strip_slack_formatting(body):
	url_regex = r'<https?:\/\/.*(?<=\|)(.*?)(?=\>)'
	matches = re.findall(url_regex, body)
	for match in matches:
		site_url_regex = r'<https?:\/\/{}\|{}>'.format(match, match)
		body = re.sub(site_url_regex, match, body)

	return body

def cmd_help():
	try:
		f = open('data/help.txt', 'r')
		help = f.read()
		f.close()
	except Exception as e:
		log('exception', e)
		return "No help document available."

	return help

# Slack
def parse_bot_commands(slack_events):
	for event in slack_events:
		if event["type"] == "message" and not "subtype" in event:
			user_id, message, full_text = parse_direct_mention(event["text"])
			if user_id == bot_id:
				return message, event["text"], event["channel"]
	return None, None, None

def parse_direct_mention(message_text):
	matches = re.search(MENTION_REGEX, message_text)
	return (matches.group(1), matches.group(2).strip(), message_text) if matches else (None, None, None)

def handle_command(command, message_text, channel):
	try:
		args = get_args(message_text)
	except Exception as e:
		log('warn', e)
		response = "Invalid arguments given."
		reply(channel, response)
		return None

	command = command.split()[0]
	if command == 'checkuser':
		response = pushshift.checkuser(args, channel)
	elif command == 'checkphrase':
		response = pushshift.checkphrase(args, channel)
	elif command == 'mega':
		response = megabot.cmd_initiate_mega(args, channel)
	elif command == 'discussion':
		response = megabot.cmd_initiate_discussion(args, channel)
	elif command == 'endthread':
		response = megabot.cmd_end_thread(args, channel)
	elif command == 'ac':
		response = factoids.cmd_get_ac()
	elif command == 'mentors':
		response = factoids.cmd_get_mentors()
	elif command == 'query':
		response = db.print_query_results(message_text.split('=', 1)[1][1:-1])
	elif command == 'poll':
		response = pollster.setup_poll(args, channel)
	elif command == "sysinfo":
		response = sysinfo.cmd_get_sysinfo(UPTIME)
	elif command == 'help':
		response = cmd_help()
	else:
		response = "Invalid command. Try again."

	if response:
		if response != True:
			reply(channel, response)

if __name__ == "__main__":
	while True:
		try:
			if slack_client.rtm_connect(with_team_state=False):
				msg = "{} connected and running!".format(config['bot_name'])
				log('info', msg)
				bot_id = slack_client.api_call("auth.test")["user_id"]
				while True:
					try:
						command, message_text, channel = parse_bot_commands(slack_client.rtm_read())
						if command:
							handle_command(command, message_text, channel)
						time.sleep(RTM_READ_DELAY)
					except (slackclient.server.SlackConnectionError, websocket._exceptions.WebSocketConnectionClosedException) as e:
						slack_client.rtm_connect(with_team_state=False)
			else:
				msg = "Connection failed. Exception traceback printed above."
				log('warn', msg)
		except(ConnectionError, TimeoutError) as e:
			log('warn', e)
			continue
