from pmb import *
from modules import domain_match, queueflood

config = get_config()

reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def process_submissions():
	submissions = subreddit.stream.submissions(skip_existing=True)
	for submission in submissions:
		if not submission.is_self:
			post_dt = pendulum.from_timestamp(submission.created_utc, tz='UTC')
			post_dt = post_dt.strftime("%Y-%m-%d %H:%M:%S")
			author_dt = pendulum.from_timestamp(submission.author.created_utc, tz='UTC')
			author_dt = author_dt.strftime("%Y-%m-%d %H:%M:%S")

			db.Submission.insert(id=submission.id,
								created_utc=post_dt,
								author=submission.author.name,
								title=submission.title,
								url=submission.url,
								flair=submission.link_flair_text,
								author_created_utc=author_dt,
								author_flair_text=submission.author_flair_text,
								author_link_karma=submission.author.link_karma,
								author_comment_karma=submission.author.comment_karma
								).execute()

			domain_match.check_domain(submission)
			queueflood.check_user(submission.author.name)

def start():
	while True:
		try:
			process_submissions()
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()