from pmb import *

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def create_post(channel, title, body, type):
	text = "Initiating thread..."
	response = reply(channel, text)

	if type == 'mega':
		flair = config['megabot']['mega_flair']
	elif type == 'discussion':
		flair = config['megabot']['discussion_flair']
	response = update(channel, "Submitting post...", response['ts'])
	post = subreddit.submit(title, selftext=body, send_replies=False)
	response = update(channel, "Approving post...", response['ts'])
	post.mod.approve()
	response = update(channel, "Flairing post...", response['ts'])
	post.mod.flair(text=flair)
	response = update(channel, "Distinguishing post...", response['ts'])
	post.mod.distinguish(how='yes')
	response = update(channel, "Stickying post...", response['ts'])
	post.mod.sticky(state=True)
	response = update(channel, "Setting suggested sort...", response['ts'])
	post.mod.suggested_sort(sort=config['megabot']['initial_sort'])
	response = update(channel, "Ignoring reports...", response['ts'])
	post.mod.ignore_reports()

	return post, response

def configure_regex(post, title, anchor, multi):
	regex = """---
### Megathread: {} ({})
title (regex): '(?=.*\\b{}\\b)(?=.*({}))'
action: report
action_reason: megathread{}""".format(title, post.id, anchor, multi, post.id)

	am = subreddit.wiki['config/automoderator']
	conf = regex + '\n\n' + am.content_md
	reason = "Add Megathread: {}".format(post.id)
	am.edit(conf, reason=reason)
	return True

def change_sort(post, sort, channel):
	post.mod.suggested_sort(sort=sort)
	text = "Sort on post *{}* changed to *{}*.".format(post.title, sort)
	reply(channel, text)

def report_posts(post, limit, anchor, multi, channel, response):
	regex = r'(?=.*\b{}\b)(?=.*({}))'.format(anchor, multi)
	count = 1
	for submission in subreddit.new(limit=limit):
		text = "Reporting submission {}/{}...".format(count, limit)
		response = update(channel, text, response['ts'])
		if not submission.is_self:
			if re.search(regex, submission.title, re.IGNORECASE):
				reason = 'megathread{}'.format(post.id)
				submission.report(reason)
		count += 1

	return True, response

def cmd_end_thread(args, channel):
	ts = pendulum.now().to_datetime_string()

	am_configured = False

	try:
		post_id = args['id']
	except Exception as e:
		log('warn', e)
		return "Post `id` not given."

	text = "Ending thread *{}*...".format(post_id)
	response = reply(channel, text)

	try:
		post = reddit.submission(post_id)
		title = post.title
		sub = post.subreddit
	except Exception as e:
		log('warn', e)
		return "Invalid post `id` given."

	if not sub == config['subreddit']:
		return "Post <https://redd.it/{}|{}> does not belong to <https://reddit.com/r/{}|/r/{}>".format(post_id, post_id, config['subreddit'], config['subreddit'])

	try:
		post.mod.sticky(state=False)
		unsticked = True
	except Exception as e:
		log('exception', e)
		unsticked = False

	try:
		am = subreddit.wiki['config/automoderator']
		regex = r"^---[\n\r]+[\S ]+[\n\r]+[\S ]+[\n\r]+[\S ]+[\n\r]+[\S ]+megathread{}[\n\r]+".format(post_id)
		regex = re.compile(regex, re.IGNORECASE|re.MULTILINE)

		conf, reps = re.subn(regex, '', am.content_md)
		reason = "End Megathread: {}".format(post_id)
		am.edit(conf, reason=reason)
		if reps > 0:
			am_configured = True
	except Exception as e:
		log('exception', e)
		am_configured = False

	text = "Thread *{}* ended.\nID: `{}`\nAM Unconfigured: {}\nUnsticked: {}".format(title, post_id, am_configured, unsticked)
	# log('info', response)
#	update(channel, text, response['ts'])
	reply(channel, text)
	return True

def cmd_initiate_mega(args, channel):
	am_configured = False
	reported = False

	ts = pendulum.now().to_datetime_string()

	try:
		title = args['title']
		body = strip_slack_formatting(args['text'])
	except Exception as e:
		log('warn', e)
		return "A megathread `title` and `text` and is required."

	try:
		anchor = args['anchor']
		multi = args['multi']
	except Exception as e:
		log('warn', e)
		return "An `anchor` and | separated list of `multis` is required."

	try:
		limit = int(args['search'])
		if limit < 1 or limit > 100:
			return "Limit must be between 1-100."
	except Exception as e:
		log('warn', e)
		return "Invalid `search` or no `search` given. An integer between 1-100 is required."

	try:
		post, response = create_post(channel, title, body, 'mega')
	except Exception as e:
		log('exception', e)
		return "Unable to create megathread. Aborting."

	try:
		response = update(channel, "Configuring AutoModerator...", response['ts'])
		am_configured = configure_regex(post, title, anchor, multi)
	except Exception as e:
		log('exception', e)
		am_configured = False

	try:
		response = update(channel, "Reporting submissions...", response['ts'])
		reported, response = report_posts(post, limit, anchor, multi, channel, response)
	except Exception as e:
		log('exception', e)
		reported = False

	text = "Megathread *{}* initiated.\nID: `{}`\nAM Configured: {}\nPosts reported: {}\nReport code: `megathread{}`\nLink: https://reddit.com{}\nExpiration: {} seconds\nSort: \"{}\" will be changed to \"{}\" after {} seconds".format(title, post.id, am_configured, reported, post.id, post.permalink, config['megabot']['expire'], config['megabot']['initial_sort'], config['megabot']['final_sort'], config['megabot']['sort_delay'])
	# log('info', text)
	update(channel, text, response['ts'])

	t1 = threading.Timer(config['megabot']['expire'], cmd_end_thread, args=[{"id" : post.id}, config['announce_channel']]).start()
	t2 = threading.Timer(config['megabot']['sort_delay'], change_sort, args=[post, config['megabot']['final_sort'], config['announce_channel']]).start()

	return True

def cmd_initiate_discussion(args, channel):
	ts = pendulum.now().to_datetime_string()
	try:
		title = args['title']
		body = strip_slack_formatting(args['text'])
	except Exception as e:
		log('warn', e)
		return "A discussion thread `title` and `text` and is required."

	try:
		post, response = create_post(channel, title, body, 'discussion')
	except Exception as e:
		log('exception', e)
		return "Unable to create discussion thread. Aborting."

	text = "Discussion thread *{}* initiated.\nID: `{}`\nLink: https://reddit.com{}\nExpiration: {} seconds".format(title, post.id, post.permalink, config['megabot']['expire'])
	# log('info', response)
	update(channel, text, response['ts'])

	t1 = threading.Timer(config['megabot']['expire'], cmd_end_thread, args=[{"id" : post.id}, config['announce_channel']]).start()

	return True
