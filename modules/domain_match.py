from pmb import *
from publicsuffixlist import PublicSuffixList

psl = PublicSuffixList()

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

channel = config['report_channel']

regex = re.compile('https?://(ww[0-9]+\.|www[0-9]*\.)?(.+?)/', re.IGNORECASE)

def check_domain(submission):
	original_domain = psl.privatesuffix(re.match(regex, submission.url)[2])
	fetched_url = requests.get(submission.url, headers={'Accept-Encoding': 'gzip, deflate'}).url
	redirect_domain = psl.privatesuffix(re.match(regex, fetched_url)[2])

	if original_domain != redirect_domain:
		out = "*[DOMAIN MISMATCH]* Submission *{}* by <https://reddit.com/user/{}/overview|/u/{}> has domain *{}* but redirects to *{}*: https://redd.it/{}".format(submission.title, submission.author, submission.author, original_domain, redirect_domain, submission.id)
		reply(channel, out)
		log('info', out)

	return