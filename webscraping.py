import praw
import re
import pandas as pd

reddit = praw.Reddit(client_id='5OIBM9csRhVFWg',
                     client_secret="jSgOYMFsmKLp5nn-fQH6OppX_E0",
                    user_agent='a script to summarize the workouts used by posters of progresspics v0.0.1 \
                    (by /u/wantthatbod for Insight Health Data Science)')


progresspics = reddit.subreddit('progresspics')
dat = pd.DataFrame(columns=["id", "imageurl", "age", "height", "startweight", "finalweight", "text"])
# real start 1325376000 (currently is only for 1 year)
for submission in progresspics.submissions(1483185599, 1514764799):
    # check if there is a picture
    url = submission.url
    if(re.search(r'comments', url)):
        continue

    # check there is a match for demographics
    match = re.search(r'(\w+)\s*/\s*(\d*)\s*/(\d+)\'*\"*(\d+)\'*\"*', submission.title)
    # check if match exists
    if (match is None):
        continue

    # check there is a match for weight
    match_w = re.search(r'\[(\d+)\s*>\s*(\d+).*\]', submission.title)
    if(match_w is None):
        continue


        # demographics
    # sanity check values:
    gender = match.group(1)
    if(gender[0].upper() != 'F'):
        continue

    age = int(match.group(2))
    if(age < 0 | age > 120):
        continue

    height_feet = int(match.group(3))
    height_inch = int(match.group(4))

    if((height_feet <= 0) | (height_feet > 9) | (height_inch <= 0) | (height_inch > 12)):
        match_check = re.search(r'(\d+)\s*cm', submission.title)

        if(match_check is None):
            continue

        height = float(match_check.group(1))/2.54
    else:
        height = height_feet*12 + height_inch

        # weight
    inkg = 1-(re.search('kg', submission.title) is None)

    if(inkg):
        startweight = float(match_w.group(1))*2.20462262
        finalweight = float(match_w.group(2))*2.20462262
    else:
        startweight = float(match_w.group(1))
        finalweight = float(match_w.group(2))

    if((startweight <= 0.0) | (finalweight <= 0.0)):
        continue

    match_time = re.search(r'.*(\d+)\s*month.*', submission.title)
    timeunit = 'month'
    if(match_time is None):
        match_time = re.search(r'.*(\d+)\s*week.*', submission.title)
        if(match_time is None):
            time = None
            timeunit = None
        else:
            time = float(match_time.group(1))
            time = time/4.333
            timeunit='week'
    else:
        time = float(match_time.group(1))

    submission.comments.replace_more(limit=None)
    comment_queue = submission.comments[:]  # Seed with top-level
        # pull remaining text
    if(timeunit == 'month'):
        match_text = re.search(r'.*/.*/.*\[.*\].*months(.*)', submission.title)
    elif(timeunit == 'week'):
        match_text = re.search(r'.*/.*/.*\[.*\].*weeks(.*)', submission.title)
    else:
        match_text = re.search(r'.*/.*/.*\[.*\](.*)', submission.title)

    if(match_text is not None):
        text = match_text.group(1) # Pull rest of the text
    else:
        text = ""

    while comment_queue:
        comment = comment_queue.pop(0)
        if (comment.author == submission.author):
            text += comment.body
        comment_queue.extend(comment.replies)

    dat = dat.append({
        "id": submission.id,
        "imageurl": url,
        "age": age,
        "height": height,
        "startweight": startweight,
        "finalweight": finalweight,
        "text": text
    }, ignore_index = True)

import os
os.chdir('/mnt/c/Users/jhyan/OneDrive/Projects/GitHub/InsightProject/WantThatBod')

dat.to_pickle("./datafor2017.pkl")