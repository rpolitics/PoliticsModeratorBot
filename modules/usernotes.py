from pmb import *

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

def process_tags(last_run):
    notes = json.loads(zlib.decompress(base64.b64decode(json.loads(subreddit.wiki['usernotes'].content_md)['blob'])))

    for author, note in notes.items():
        note = note['ns'][0]
        tag = note['n']
        ts = pendulum.from_timestamp(note['t'], tz='UTC')
        loc = note['l'].split(',')

        try:
            submission_id = loc[1]
        except IndexError:
            continue

        try:
            comment_id = loc[2]
        except IndexError:
            continue

        if submission_id and comment_id:
            if ts > last_run:
                if tag in config['removals']['tags'].keys():
                    comment = reddit.comment(comment_id)
                    permalink = '/r/politics/comments/{}/-/{}/'.format(submission_id, comment_id)

                    reason = config['removals']['reasons'][config['removals']['tags'][tag]]
                    reply = format_removal_reply(reason, author, permalink, "comment")

                    try:
                        comment = comment.reply(reply)
                        comment.mod.distinguish()
                        comment.mod.lock()
                    except praw.exceptions.APIException as e:
                        if e.error_type == 'DELETED_COMMENT':
                            continue

def start():
    last_run = pendulum.now('UTC')
    while True:
        try:
            process_tags(last_run)
            last_run = pendulum.now('UTC')
            time.sleep(60)
        except Exception as e:
            log('exception', e)

t = Thread(target=start)
t.daemon = True
t.start()