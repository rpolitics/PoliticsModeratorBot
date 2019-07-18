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
	analyze_request = { 'comment': { 'text': body }, 'clientToken' : id, 'requestedAttributes': {k: {} for k in config['perspective']['attributes']}, 'languages' : ['en'] }
	response = perspective.comments().analyze(body=analyze_request).execute()
	scores = {}
	attributeScores = response['attributeScores']
	for attribute in config['perspective']['attributes']:
		scores[attribute.lower()] = float(attributeScores[attribute]['summaryScore']['value'])
	return scores

# PRAW Processing
def process_comment(comment):
	try:
		scores = get_scores(comment.id, comment.body)
	except googleapiclient.errors.HttpError:
		out = '*[PERSPECTIVE]* Unable to get perspective on comment ' + comment.id
		log('warn', out)
		return

	scores['id'] = comment.id

	db.Perspective.insert(scores).execute()

	return