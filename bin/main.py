#!/usr/bin/env python
"""
Reddit Deckstring Bot
https://www.reddit.com/r/redditdev/comments/5tmetp/get_stream_of_both_submissions_and_comments/
"""

import os, sys; sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa isort:skip
import argparse
from datetime import datetime, timedelta
from time import sleep

import praw
from praw.models import Message
from deck_code_bot.main import find_and_decode_deckstrings, make_reply, markdown_link


USER_AGENT = os.getenv(
    "DCB_USER_AGENT",
    "deck-code-bot v2.0 (https://github.com/HearthSim/deck-code-bot)"
)
CLIENT_ID = os.getenv("DCB_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DCB_CLIENT_SECRET", "")
USERNAME = os.getenv("DCB_USERNAME", "deck-code-bot")
PASSWORD = os.getenv("DCB_PASSWORD", "")

SUBREDDITS = os.getenv("DCB_SUBREDDITS", "DeckCodeBotTest")


def init_reddit():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "You need to define DCB_CLIENT_ID and DCB_CLIENT_SECRET environment variables."
        )
    bot = praw.Reddit(
        user_agent=USER_AGENT,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        username=USERNAME,
        password=PASSWORD,
    )

    return bot


_cached_blocklist = None
_blocklist_ts = 0


def get_cached_blocklist(reddit):
    global _cached_blocklist
    global _blocklist_ts
    if _blocklist_ts < int(datetime.utcnow().timestamp()) - 600:
        _cached_blocklist = None

    if _cached_blocklist is None:
        _cached_blocklist = reddit.user.blocked()
        _blocklist_ts = int(datetime.utcnow().timestamp())

    return _cached_blocklist


def is_blacklisted(reddit, user) -> bool:
    return str(user).lower() in [USERNAME.lower()] + [
        str(u).lower() for u in get_cached_blocklist(reddit)
    ]


def comment_stream(reddit):
    for comment in reddit.subreddit(SUBREDDITS).stream.comments():
        text = getattr(comment, "body", "").strip()
        created_time = datetime.utcfromtimestamp(comment.created_utc)

        def callback(decks):
            # Check if we already replied to the comment
            replies = comment.replies
            if USERNAME.lower() in [str(reply.author).lower() for reply in replies]:
                return

            reply_text = ""
            if len(decks) == 1:
                full_thread = comment.submission
                deckstring = decks[0]._deckstring
                for other_comment in full_thread.comments.list():
                    # Look for our own comments in the post
                    if str(other_comment.author).lower() != USERNAME.lower():
                        continue

                    # Is the deckstring present in the post?
                    if deckstring in other_comment.body:
                        reply_text = markdown_link(
                            "Click here for decklist", other_comment.permalink
                        )
                        break

            if not reply_text:
                reply_text = make_reply(decks, locale="enUS")

            comment.reply(reply_text)

        yield text, comment.author, created_time, callback


def submission_stream(reddit):
    for submission in reddit.subreddit(SUBREDDITS).stream.submissions():
        text = getattr(submission, "selftext", "").strip()
        created_time = datetime.utcfromtimestamp(submission.created_utc)

        def callback(decks):
            comments = submission.comments
            # Check whether we already replied to the post
            if USERNAME.lower() in [str(comment.author).lower() for comment in comments]:
                return

            reply_text = make_reply(decks, locale="enUS")
            submission.reply(reply_text)

        yield text, submission.author, created_time, callback


def pm_stream(reddit):
    for item in reddit.inbox.stream():
        if not isinstance(item, Message):
            # Ignore comment replies, notifications, etc
            continue
        text = getattr(item, "body", "").strip()
        created_time = datetime.utcfromtimestamp(item.created_utc)

        def callback(decks):
            reply_text = make_reply(decks, locale="enUS")
            item.reply(reply_text)

        item.mark_read()

        yield text, item.author, created_time, callback


def run_stream_loop(reddit, stream, args):
    while True:
        for text, author, created_time, callback in stream:
            if created_time < datetime.utcnow() - timedelta(seconds=args.max_age):
                continue

            if not text:
                continue

            if is_blacklisted(reddit, author):
                continue

            decks = find_and_decode_deckstrings(text)
            if not decks:
                continue

            callback(decks)

        # We shouldn't reach this, but just in case...
        sleep(5)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="*")
    p.add_argument("--locale", default="enUS")
    p.add_argument("--stream", default="local", choices=[
        "local", "comments", "submissions", "pms"
    ])
    p.add_argument("--max-age", type=int, default=120)
    args = p.parse_args(sys.argv[1:])

    if args.stream == "local":
        for file_name in args.files:
            with open(file_name, "r") as f:
                decks = find_and_decode_deckstrings(f.read())
                print(make_reply(decks, locale=args.locale))
        return 0

    reddit = init_reddit()

    if args.stream == "comments":
        stream = comment_stream(reddit)
    elif args.stream == "submissions":
        stream = submission_stream(reddit)
    elif args.stream == "pms":
        stream = pm_stream(reddit)

    try:
        run_stream_loop(reddit, stream, args)
    except KeyboardInterrupt:
        sys.stderr.write("Aborted!\n")
        return 1


if __name__ == "__main__":
    exit(main())
