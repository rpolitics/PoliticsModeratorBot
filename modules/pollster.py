#!/usr/bin/env python3

from pmb import *

import pandas

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

dateparse = lambda x: pandas.datetime.strptime(x, '%m/%d/%y %H:%M')

df = pandas.read_csv('https://projects.fivethirtyeight.com/polls-page/president_primary_polls.csv', usecols=['poll_id', 'question_id', 'state', 'pollster', 'created_at', 'party', 'answer', 'pct', 'url'], parse_dates=['created_at'], date_parser=dateparse)
df['id'] = df.poll_id + df.question_id

start_date = (datetime.datetime.now() + datetime.timedelta(-14)).strftime('%m/%d/%y')

all_polls = df.loc[df.created_at >= start_date]

polls = {}

def create_post(channel, title, beforetext, aftertext, table):
    msg = "Initiating poll..."
    response = reply(channel, msg)

    body = '{}\n\n{}\n\n{}'.format(beforetext, table, aftertext)

    response = update(channel, "Submitting post...", response['ts'])
    post = subreddit.submit(title, selftext=body, send_replies=False)
    response = update(channel, "Approving post...", response['ts'])
    post.mod.approve()
    response = update(channel, "Distinguishing post...", response['ts'])
    post.mod.distinguish(how='yes')
    response = update(channel, "Stickying post...", response['ts'])
    post.mod.sticky(state=True)
    response = update(channel, "Ignoring reports...", response['ts'])
    post.mod.ignore_reports()

    msg = "Polling thread *{}* initiated: https://reddit.com{}".format(title, post.permalink)
    update(channel, msg, response['ts'])

    return True

def process_polls(polls, candidates):
    data = {}

    keep_candidates = candidates

    for id in polls.id.unique():

        poll = polls.loc[polls['id'] == id]

        data[id] = {}
        data[id]['candidates'] = {}

        i = 0
        for idx, row in poll.iterrows():
            created_at = pandas.to_datetime(row.created_at).strftime('%-m-%-d')
            data[id]['state'] = row.state if not pandas.isnull(row.state) else 'National'
            data[id]['created_at'] = created_at
            data[id]['pollster'] = row.pollster.split('/')[0]
            data[id]['candidates'][row.answer] = int(row.pct)
            data[id]['url'] = row.url.replace(')','\)')

        known_candidates = data[id]['candidates'].keys()

        for candidate in candidates:
            if candidate not in known_candidates:
                data[id]['candidates'][candidate] = '--'

        sorted_data = {}
        sorted_candidates = sorted(data[id]['candidates'])
        for candidate in sorted_candidates:
            sorted_data[candidate] = data[id]['candidates'][candidate]

        data[id]['candidates'] = sorted_data

    keep_data = data
    for key in data.copy().keys():
        for k in data[key]['candidates'].copy().keys():
            if k not in keep_candidates:
                del keep_data[key]['candidates'][k]

    return data

def generate_table(polls, candidates):
    table = "Poll|Date|Type|{}\n".format('|'.join(sorted(candidates)))
    table += ":--|:--|:--|:--{}\n".format('|:--' * len(candidates))

    for poll in polls.items():
        poll = poll[1]
        table += "[{}]({})|{}|{}|".format(poll['pollster'], poll['url'], poll['created_at'], poll['state'])
        table += '|'.join(str(x) for x in poll['candidates'].values())
        table += '\n'

    return table

def generate_poll(party, candidates):
    polls[party] = all_polls.loc[all_polls['party'] == party].sort_values(by=['created_at'], ascending=False)

    data = process_polls(polls[party], candidates)

    table = generate_table(data, candidates)

    return table

def setup_poll(args, channel):
    try:
        title = args['title']
    except Exception as e:
        log('warn', e)
        return "No `title` given."

    try:
        beforetext = args['beforetext']
        aftertext = args['aftertext']
    except Exception as e:
        log('warn', e)
        return "No `beforetext` and `aftertext` given."

    try:
        party = args['party']
    except Exception as e:
        log('warn', e)
        return "No `party` given."

    try:
        candidates = args['candidates'].split(',')
    except Exception as e:
        log('warn', e)
        return "No `candidates` given."

    table = generate_poll('DEM', candidates)

    create_post(channel, title, beforetext, aftertext, table)