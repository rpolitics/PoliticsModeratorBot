#!/usr/bin/env python3

from pmb import *

import pandas

config = get_config()

# PRAW
reddit = praw.Reddit(config['bot_name'], user_agent=config['user_agent'])
subreddit = reddit.subreddit(config['subreddit'])

dateparse = lambda x: datetime.datetime.strptime(x, '%m/%d/%y %H:%M')

def create_file(channel, table):
    f = open("polls.txt", "w")
    f.write(table)
    f.close()

    f = open("polls.txt", "r")
    upload(channel, f, "polls")
    f.close()
    os.remove("polls.txt")

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
            created_at = (row.created_at).strftime('%-m-%-d')
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

def generate_polls(candidates, days):
    df = pandas.read_csv('https://projects.fivethirtyeight.com/polls-page/president_polls.csv', usecols=['poll_id', 'question_id', 'state', 'pollster', 'created_at', 'answer', 'pct', 'url'], parse_dates=['created_at'], date_parser=dateparse)
    df['id'] = df.poll_id + df.question_id

    start_date = (datetime.datetime.now() + datetime.timedelta(-days)).strftime('%m/%d/%y')

    all_polls = df.loc[df.created_at >= start_date]

    polls = {}
    polls = all_polls.sort_values(by=['created_at'], ascending=False)

    data = process_polls(polls, candidates)

    table = generate_table(data, candidates)

    return table

def setup_poll(args, channel):
    try:
        candidates = args['candidates'].split(',')
    except Exception as e:
        log('warn', e)
        return "No `candidates` given."

    try:
        days = int(args['days'])
    except Exception as e:
        log('warn', e)
        return "You must enter a valid number of days from today to obtain polls."

    table = generate_polls(candidates, days)

    create_file(channel, table)

    return True