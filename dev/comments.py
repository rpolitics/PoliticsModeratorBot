from pmb import *
# from modules import perspective

config = get_config()

reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def process_comments():
	comments = subreddit.stream.comments(skip_existing=True)
	for comment in comments:
		submission_id = get_id(comment.link_id)
		post_dt = pendulum.from_timestamp(comment.created_utc, tz='UTC')
		author_dt = pendulum.from_timestamp(comment.author.created_utc, tz='UTC')
		db.Comment.insert(id=comment.id,
							submission_id=submission_id,
							created_utc=post_dt,
							author=comment.author.name,
							comment=comment.body,
							author_created_utc=author_dt,
							author_flair_text=comment.author_flair_text,
							author_link_karma=comment.author.link_karma,
							author_comment_karma=comment.author.comment_karma
							).execute()

		# perspective.process_comment(comment)

def start():
	while True:
		try:
			process_comments()
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()