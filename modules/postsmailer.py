from pmb import *

config = get_config()

TIME_LIMIT = config['postsmailer']['timelimit']

reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])

subreddits = config['postsmailer']['subreddits']

def generate_message(subreddit, posts):
	subject = subreddit

	posts = posts[::-1]
	posts = '\n'.join([str(x+1) + '. [' + pendulum.from_timestamp(posts[x].created_utc, tz='local').to_datetime_string() + ' UTC] [' + posts[x].title + '](https://redd.it/' + posts[x].id + ') by /u/' + posts[x].author.name for x in range(len(posts))])

	body = "# Last Week in /r/{}\n\n## The following new submissions were posted within the last week on /r/{}:\n\n{}\n\nPlease be sure to weigh in on any brainstorms or props, review new results, and cast your vote in any open votes.".format(subreddit, subreddit, posts)

	reddit.redditor('mod_mailer').message(subject, body)

def get_newest_posts(subreddit):
	posts = []
	now = pendulum.now('UTC').timestamp()
	for submission in reddit.subreddit(subreddit).new():
		age = now - submission.created_utc
		if age > TIME_LIMIT:
			break

		posts.append(submission)

	if len(posts) > 0:
		generate_message(subreddit, posts)

def job():
	for subreddit in subreddits:
		get_newest_posts(subreddit)

def start():
	schedule.every().monday.at("03:00").do(job)
	while True:
		try:
			schedule.run_pending()
			time.sleep(600)
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()