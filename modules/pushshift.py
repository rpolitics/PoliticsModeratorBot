from pmb import *
from psaw import PushshiftAPI

config = get_config()

ps = PushshiftAPI()


def checkuser(args, channel):
	try:
		user = args['user']
	except:
		return "No user given."

	response = ""

	submissions = ps.search_submissions(author=user, subreddit='politics', limit=10, filter=['created_utc', 'title', 'permalink', 'id'])
	response += '*SUBMISSIONS*\n'
	for submission in submissions:
		ts = pendulum.from_timestamp(submission.created_utc, tz='UTC').to_datetime_string()
		out = '- *{}*: "{}" <https://reddit.com{}|Post> | <http://api.pushshift.io/reddit/search/submission/?ids={}|Archive>'.format(ts, submission.title, submission.permalink, submission.id)
		response += out + '\n'

	response += '\n'

	comments = ps.search_comments(author=user, subreddit='politics', limit=10, filter=['created_utc', 'body', 'permalink', 'id'])
	response += '*COMMENTS*\n'
	for comment in comments:
		ts = pendulum.from_timestamp(comment.created_utc, tz='UTC').to_datetime_string()

		if len(comment.body) <= 100:
			text = comment.body
		else:
			text = comment.body[:100] + '...'

		out = '- *{}*: "{}" <https://reddit.com{}|Comment> | <https://api.pushshift.io/reddit/comment/search?ids={}|Archive>'.format(ts, text, comment.permalink, comment.id)

		response += out + '\n'

	return response
