from pmb import *

from googleapiclient import discovery
import googleapiclient
import uuid
import logging

logging.getLogger("googleapiclient").setLevel(logging.WARNING)

config = get_config()

# Perspective Processing
def get_scores(comment):
	id = comment.id
	body = comment.body

	first_keys = {k for k in config['perspective']['report'].keys()}
	second_keys = {k for k in config['perspective']['remove'].keys()}
	keys = first_keys.union(second_keys)

	perspective = discovery.build('commentanalyzer', 'v1alpha1', developerKey=config['perspective']['api_key'], cache_discovery=False)
	analyze_request = { 'comment': { 'text': body }, 'clientToken' : id, 'requestedAttributes': {k: {} for k in keys}, 'languages' : ['en'], "clientToken" : id }
	response = perspective.comments().analyze(body=analyze_request).execute()
	scores = {}
	all_scores = {}
	attributeScores = response['attributeScores']
	for attr, threshold in config['perspective']['report'].items():
		score = float(attributeScores[attr]['summaryScore']['value'])
		if score >= threshold:
			scores[attr] = score
		all_scores[attr] = score

	for attr, threshold in config['perspective']['remove'].items():
		score = float(attributeScores[attr]['summaryScore']['value'])
		if score >= threshold:
			dt = pendulum.now('UTC').to_datetime_string()
			target_fullname = 't1_' + comment.id
			reason = attr + " " + str(score)

			db.BotLog.insert(id=target_fullname, module='perspective', created_utc=dt, action='removecomment', details=reason, author=comment.author, body=comment.body).execute()

			comment.mod.remove()

	return scores, all_scores

# PRAW Processing
def process_comment(comment):
	try:
		scores, all_scores = get_scores(comment)
	except googleapiclient.errors.HttpError:
		out = '*[PERSPECTIVE]* Unable to get perspective on comment ' + comment.id
		log('warn', out)
		return

	if not scores:
		return

	if not config['perspective']['report']:
		return

	score_text = []

	for attr, score in scores.items():
		threshold = config['perspective']['report'][attr]
		text = "*{}* ({:.2f}/{:.2f})".format(attr, score, threshold)
		score_text.append(text)

	link_id = get_id(comment.link_id)
	out = "*[PERSPECTIVE]* Comment *<https://reddit.com/r/{}/comments/{}/-/{}/|{}>* by *<https://reddit.com/user/{}/overview|/u/{}>* exceeds Perspective thresholds: {}".format(config['subreddit'], link_id, comment.id,  comment.id, comment.author, comment.author, ', '.join(score_text))
	reply(config['perspective']['channel'], out)
	# log('info', out)

	dt = pendulum.from_timestamp(comment.created_utc, tz='UTC')
	target_fullname = 't1_' + comment.id
	db.Perspective.insert(id=target_fullname, created_utc=dt, author=comment.author, scores=all_scores, body=comment.body).execute()

	return
