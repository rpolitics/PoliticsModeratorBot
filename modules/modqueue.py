from pmb import *

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

COMMENT_THRESHOLD = config['reporter']['comment_threshold']
SUBMISSION_THRESHOLD = config['reporter']['submission_threshold']
REPORTED = []

def monitor_reports():
	for item in subreddit.mod.modqueue(limit=None):
		id = item.name
		for report in item.user_reports:
			reason = report[0]
			if reason:
				count = report[1]
				author = 'User'
				db.Report.insert(id=id, author=author, reason=reason, count=count, is_ignored=item.ignore_reports).on_conflict(update={'count': db.fn.GREATEST(count, db.fn.VALUES(db.Report.count))}).execute()

		for report in item.mod_reports:
			reason = report[0]
			if reason:
				author = report[1]
				db.Report.insert(id=id, author=author, reason=reason, is_ignored=item.ignore_reports).on_conflict_ignore(ignore=True).execute()

		ts = pendulum.now().to_datetime_string()

		if type(item) == praw.models.reddit.submission.Submission:
			item_type = "Submission"
			threshold = SUBMISSION_THRESHOLD
		elif type(item) == praw.models.reddit.comment.Comment:
			item_type = "Comment"
			threshold = COMMENT_THRESHOLD

		if item.id not in REPORTED:
			if item.num_reports >= threshold:
				REPORTED.append(item.id)
				if item_type == "Submission":
					out = "*[REPORTS]* {} \"{}\" by <https://reddit.com/user/{}/overview|/u/{}> has *{}*/{} reports: https://redd.it/{}".format(item_type, item.title, item.author, item.author, item.num_reports, threshold, item.id)
				elif item_type == "Comment":
					post_id = get_id(item.link_id)
					out = "*[REPORTS]* {} by <https://reddit.com/user/{}/overview|/u/{}> has *{}*/{} reports: https://www.reddit.com/r/{}/comments/{}/-/{}/".format(item_type, item.author, item.author, item.num_reports, threshold, config['subreddit'], post_id, item.id)
				reply(config['report_channel'], out)
				# log('info', out)

def start():
	while True:
		try:
			monitor_reports()
			time.sleep(60)
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()
