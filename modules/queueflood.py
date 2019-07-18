from pmb import *

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])

BURST_MAX_SECONDS = config['queueflood']['burst_max_seconds']
DAILY_SECONDS = config['queueflood']['daily_seconds']
DAILY_COUNT_LIMIT = config['queueflood']['daily_count_limit']

def remove_submission(submissions):
	submission = reddit.submission(submissions[0]['id'])
	submission.mod.remove()
	submission.mod.flair(text=config['queueflood']['flair'])

	reply = format_removal_reply(config['removals']['reasons'][config['queueflood']['flair']], submissions[0]['author'], 'https://redd.it/' + submissions[0]['id'])
	flood_links = [str(x+1) + '. [' + pendulum.from_timestamp(submissions[x]['created_utc'].timestamp(), tz='local').to_datetime_string() + ' UTC] [' + submissions[x]['title'] + '](https://redd.it/' + submissions[x]['id'] + ')' for x in range(len(submissions))]
	reply = reply.replace("{flood_links}", '\n'.join(flood_links))

	comment = submission.reply(reply)
	comment.mod.distinguish()

	db.Removal.insert(submission_id=submission.id, comment_id=comment.id, moderator=reddit.user.me(), flair=config['queueflood']['flair'], is_active=True).execute()

def check_burst(submissions):
	first_timestamp = submissions[0]['created_utc'].timestamp()
	second_timestamp = submissions[1]['created_utc'].timestamp()

	submission_burst_time_diff = first_timestamp - second_timestamp

	if submission_burst_time_diff < BURST_MAX_SECONDS:
		burst_max_dur = pendulum.duration(seconds=BURST_MAX_SECONDS)
		submissions_diff_dur = pendulum.duration(seconds=submission_burst_time_diff)

		remove_submission(submissions)

		out = "*[QUEUE FLOOD]* <https://reddit.com/user/{}/overview|/u/{}> submitted 2 items within {}m{}s (limit: {}m{}s): (1) https://redd.it/{} (2) https://redd.it/{}. Submission https://redd.it/{} has been removed.".format(submissions[0]['author'], submissions[0]['author'], submissions_diff_dur.minutes, submissions_diff_dur.remaining_seconds, burst_max_dur.minutes, burst_max_dur.remaining_seconds, submissions[0]['id'], submissions[1]['id'], submissions[0]['id'])

		# reply(config['report_channel'], out)
		log('info', out)

		return True

	return False

def check_daily(submissions):
	newest_timestamp = submissions[0]['created_utc'].timestamp()
	oldest_timestamp = submissions[DAILY_COUNT_LIMIT]['created_utc'].timestamp()

	daily_submissions_diff = newest_timestamp - oldest_timestamp

	if daily_submissions_diff < DAILY_SECONDS:
		daily_dur = pendulum.duration(seconds=DAILY_SECONDS)
		daily_submissions_diff_dur = pendulum.duration(seconds=daily_submissions_diff)

		remove_submission(submissions)

		links = ', '.join(['(' + str(x+1) + ') ' + 'https://redd.it/' + submissions[x]['id'] for x in range(len(submissions))])
		out = "*[DAILY SUBMISSION LIMIT]* <https://reddit.com/user/{}/overview|/u/{}> submitted {} items within {}h{}m{}s (limit: {} items in {}h{}m{}s): {}. Submission https://redd.it/{} has been removed.".format(submissions[0]['author'], submissions[0]['author'], len(submissions), daily_submissions_diff_dur.hours, daily_submissions_diff_dur.minutes, daily_submissions_diff_dur.remaining_seconds, DAILY_COUNT_LIMIT, int(DAILY_SECONDS/3600), daily_dur.minutes, daily_dur.remaining_seconds, links, submissions[0]['id'])

		# reply(config['report_channel'], out)
		log('info', out)

def check_user(author):
	submissions = db.Submission.select(db.Submission.id, db.Submission.author, db.Submission.created_utc, db.Submission.title).where(db.Submission.author==author, db.Submission.is_removed==False).order_by(db.Submission.created_utc.desc()).limit(DAILY_COUNT_LIMIT+1).dicts()
	if len(submissions) > 1:
		is_burst = check_burst(submissions[:2])
	if len(submissions) == DAILY_COUNT_LIMIT+1 and not is_burst:
		check_daily(submissions)

	return