from pmb import *
from modules import removals

config = get_config()

reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def process_modlog():
	modlogs = praw.models.util.stream_generator(functools.partial(subreddit.mod.log), attribute_name='id', skip_existing=True)
	for modlog in modlogs:
		dt = pendulum.from_timestamp(modlog.created_utc, tz='UTC')
		db.ModAction.insert(id=modlog.id,
					created_utc=dt,
					moderator=modlog._mod,
					action=modlog.action,
					details=modlog.details,
					target_fullname=modlog.target_fullname,
					target_author=modlog.target_author,
					target_title=modlog.target_title
					).execute()

		if modlog.action == 'approvelink':
			id = get_id(modlog.target_fullname)
			db.Submission.update(is_removed=False).where(db.Submission.id==id).execute()
		elif modlog.action == 'removelink':
			id = get_id(modlog.target_fullname)
			db.Submission.update(is_removed=True).where(db.Submission.id==id).execute()
		elif modlog.action == 'approvecomment':
			id = get_id(modlog.target_fullname)
			db.Comment.update(is_removed=False).where(db.Comment.id==id).execute()
		elif modlog.action == 'removecomment':
			id = get_id(modlog.target_fullname)
			db.Comment.update(is_removed=True).where(db.Comment.id==id).execute()
		elif modlog.action == 'editflair':
			id = get_id(modlog.target_fullname)
			flair = reddit.submission(id).link_flair_text
			db.Submission.update(flair=flair).where(db.Submission.id==id).execute()
			removals.process_flair(id, modlog._mod)

		if modlog.mod in config['reporter']['moderators']:
			out = "*[MODERATOR]* Action *{}* performed by *{}* on *<https://reddit.com/user/{}/overview|/u/{}>*: https://reddit.com{}".format(modlog.action, modlog.mod, modlog.target_author, modlog.target_author, modlog.target_permalink)
			reply(config['report_channel'], out)
			# log('info', out)

def start():
	while True:
		try:
			process_modlog()
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()
