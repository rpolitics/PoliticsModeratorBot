from pmb import *

reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def process_conversation(conversation):
	db.Conversation.insert(id=conversation.id, created_utc=conversation.created_utc, subject=conversation.subject).on_conflict_ignore(ignore=True).execute()

	for message in conversation.messages:
		dt = pendulum.from_timestamp(message.created_utc, tz='UTC')
		db.message.insert(conversation_id=conversation.id, message_id=message.id, created_utc=dt, author=message.author.name, body=message.body_markdown, is_internal=message.is_internal).on_conflict_ignore(ignore=True).execute()

		# log

while True:
	try:
		for conversation in sub.modmail.conversations(sort="recent", state="all"):
				process_conversation(conversation)
		time.sleep(30)
		for conversation in sub.modmail.conversations(sort="recent", state="mod"):
				process_conversation(conversation)
		time.sleep(30)
		for conversation in sub.modmail.conversations(sort="recent", state="archived"):
				process_conversation(conversation)
		time.sleep(30)
	except Exception as e:
		print(e)

def start():
	while True:
		try:
			process_submissions()
		except Exception as e:
			log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()