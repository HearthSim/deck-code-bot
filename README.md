# deck-code-bot

[![Build Status](https://api.travis-ci.org/HearthSim/deck-code-bot.svg?branch=master)](https://travis-ci.org/HearthSim/deck-code-bot)

A bot for decoding Hearthstone deck codes on Reddit

https://www.reddit.com/user/deck-code-bot

Welcome to version 2.0 of deck-code-bot! This bot checks comments and submissions from /r/hearthstone, /r/CompetitiveHS, and
a few other subreddits for deck codes (also known as deckstrings), which are the Base64 strings of characters that encode
Hearthstone decks and enable them to be shared among players. Ordinarily, to see the contents of a deck encoded in a deck code,
one would need to open one's Hearthstone client, import the code, and let the game populate the deck with cards. But with
deck-code-bot, simply pasting the code into a comment, submission, or PM will trigger a reply with a nicely-formatted list of
cards, along with card images and helpful links for HSReplay.net and the Hearthstone Wiki.

If you post two or more deck codes in the same post, deck-code-bot will attempt to return as many card lists as it can, up to
the reddit comment/PM character limit (10,000). For ordinary 30-card decks, usually just one or two lists will fit.

If you want deck-code-bot to ignore your post, just include three hash symbols (###) somewhere in the text body, and the bot
will skip over it. This escape character was chosen because when pasting a deck code directly from the game, the full deck list
is included with a single "#" in front of each card name, and with "###" in front of the deck name. Replying to each of these
"full" copied deck lists could lead to a lot of clogged comment sections.

Currently the bot only looks at English-speaking subreddits, but there is infrastructure in place to expand to non-English-
speaking Hearthstone fans. Stay tuned!

Thanks and enjoy,

Will

https://www.reddit.com/user/ziphion


## Running the tests

To run the tests, install tox (`pip install tox`) and run `tox`.
