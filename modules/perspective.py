from pmb import *

from googleapiclient import discovery
import googleapiclient
import uuid
import logging

logging.getLogger("googleapiclient").setLevel(logging.WARNING)

config = get_config()

# Perspective Processing
def get_scores(id, body):
	perspective = discovery.build('commentanalyzer', 'v1alpha1', developerKey=config['perspective']['api_key'], cache_discovery=False)
	analyze_request = { 'comment': { 'text': body }, 'clientToken' : id, 'requestedAttributes': {k: {} for k in config['perspective']['attributes'].keys()}, 'languages' : ['en'] }
	response = perspective.comments().analyze(body=analyze_request).execute()
	scores = {}
	attributeScores = response['attributeScores']
	for attr, threshold in config['perspective']['attributes'].items():
		score = float(attributeScores[attr]['summaryScore']['value'])
		if score >= threshold:
			scores[attr] = score
	return scores

# PRAW Processing
def process_comment(comment):
	try:
		scores = get_scores(comment.id, comment.body)
	except googleapiclient.errors.HttpError:
		out = '*[PERSPECTIVE]* Unable to get perspective on comment ' + comment.id
		log('warn', out)
		return

	if not scores:
		return

	score_text = []

	for attr, score in scores.items():
		threshold = config['perspective']['attributes'][attr]
		text = "*{}* ({:.2f}/{:.2f})".format(attr, score, threshold)
		score_text.append(text)

	link_id = get_id(comment.link_id)
	out = "*[PERSPECTIVE]* Comment *<https://reddit.com/r/{}/comments/{}/-/{}/|{}>* by *<https://reddit.com/user/{}/overview|/u/{}>* exceeds Perspective thresholds: {}".format(config['subreddit'], link_id, comment.id,  comment.id, comment.author, comment.author, ', '.join(score_text))
	reply(config['perspective']['channel'], out)
	# log('info', out)

	return
