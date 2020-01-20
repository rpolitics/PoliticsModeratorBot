from pmb import *

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def remove_old_comments(submission):
	comments = db.Removal.select(db.Removal.comment_id).where(db.Removal.is_active==True, db.Removal.submission_id==submission.id)
	for comment in comments.dicts():
		if comment['comment_id']:
			comment = reddit.comment(comment['comment_id'])
			comment.mod.remove()

	db.Removal.update(is_active=False).where(db.Removal.is_active==True, db.Removal.submission_id==submission.id).execute()

def new_comment(submission, mod):
		flair = submission.link_flair_text

		if flair in config['removals']['reasons'].keys():
			reply = format_removal_reply(config['removals']['reasons'][flair], submission.author, submission.permalink, "submission")

			comment = submission.reply(reply)
			comment.mod.distinguish()

			db.Removal.insert(submission_id=submission.id, comment_id=comment.id, moderator=mod, flair=flair, is_active=True).execute()

			out = "*[CHANGE FLAIR]* Submission <https://redd.it/{}|{}> by <https://reddit.com/user/{}/overview|/u/{}> had flair changed to {} by <https://www.reddit.com/r/politics/about/log/?mod={}|/u/{}>".format(submission.id, submission.id, submission.author, submission.author, flair.upper(), mod, mod)
			log('info', out)

		elif not flair:
			db.Removal.insert(submission_id=submission.id, moderator=mod, flair=flair, is_active=True).execute()

			out = "*[REMOVE FLAIR]* Submission <https://redd.it/{}|{}>  by <https://reddit.com/user/{}/overview|/u/{}> had flair REMOVED by <https://www.reddit.com/r/politics/about/log/?mod={}|/u/{}>".format(submission.id, submission.id, submission.author, submission.author, mod, mod)
			log('info', out)

def process_flair(id, mod):
	if mod not in config['removals']['exemptmods']:
		submission = reddit.submission(id=id)
		remove_old_comments(submission)
		new_comment(submission, mod)

	return
