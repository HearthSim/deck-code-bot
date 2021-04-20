import string
from urllib.parse import quote

from hearthstone.cardxml import load_dbf
from hearthstone.deckstrings import Deck
from hearthstone.enums import ZodiacYear, get_localized_name


base64_alphabet = string.ascii_letters + string.digits + "+/= \n#"

MAX_CHARACTERS = 10000

I_AM_A_BOT = " ^".join(
    """
^I am a bot. Comment/PM with a deck code and I'll decode it. If you
don't want me to reply to you, include \"###\" anywhere in your message.
[About.](https://github.com/HearthSim/deck-code-bot/blob/master/README.md)
""".strip().split()
)


def remove_non_b64(text):
    return "".join(k for k in text if k in base64_alphabet)


def find_and_decode_deckstrings(text):
    b64_text = remove_non_b64(text)
    decks = []
    for chunk in b64_text.split():
        if any(word in chunk for word in ["###", "#\\#\\#"]):
            return []
        if not chunk.startswith(("AAEBA", "AAECA")):
            continue
        if chunk in [deck._deckstring for deck in decks]:
            continue
        try:
            deck = Deck.from_deckstring(chunk)
        except Exception:
            continue

        deck._deckstring = chunk
        decks.append(deck)

    return decks


def pretty_zodiac_year(year):
    """
    Returns the Zodiac year in English
    """
    return {
        ZodiacYear.INVALID: "(unknown)",
        ZodiacYear.PRE_STANDARD: "Vanilla",
        ZodiacYear.KRAKEN: "Year of the Kraken",
        ZodiacYear.MAMMOTH: "Year of the Mammoth",
        ZodiacYear.RAVEN: "Year of the Raven",
        ZodiacYear.DRAGON: "Year of the Dragon",
        ZodiacYear.PHOENIX: "Year of the Phoenix",
        ZodiacYear.GRYPHON: "Year of the Gryphon",
    }.get(year, "(unknown)")


def tabulate(rows, headers=None):
    ret = []
    if headers:
        ret.append(" | ".join(headers))
        ret.append(":--:|:---|:--:|:--:")

    for row in rows:
        ret.append(" | ".join(str(c) for c in row))

    return "\n".join(ret)


def markdown_link(text, url):
    text = text.replace("]", r"\]")
    return f"[{text}]({url})"


def calculate_reply_length(reply_chunks):
    return len("\n".join(reply_chunks + [I_AM_A_BOT]))


def make_reply(decks, locale="enUS"):
    db, _ = load_dbf(locale=locale)
    if locale != "enUS":
        english_db, _ = load_dbf(locale="enUS")  # For Gamepedia links
    else:
        english_db = db

    reply = []

    for deck in decks:
        reply_chunks = []

        card_includes = deck.cards
        cards = [(db[dbf_id], count) for dbf_id, count in card_includes]
        cards.sort(key=lambda include: (include[0].cost, include[0].name))
        try:
            hero = db[deck.heroes[0]]
            class_name = get_localized_name(hero.card_class, locale=locale)
            hero_name = f"{class_name} ({hero.name})"
        except KeyError:
            hero_name = "Unknown"

        format_name = get_localized_name(deck.format, locale=locale)
        standard_year_name = pretty_zodiac_year(ZodiacYear.as_of_date())

        reply_chunks.append(f"**Format:** {format_name} ({standard_year_name})\n")
        reply_chunks.append(f"**Class:** {hero_name}\n")

        rows = []

        for card, count in cards:
            english_card = english_db[card.dbf_id]
            image = get_card_image(card, locale)
            rows.append(
                (
                    card.cost,
                    markdown_link(card.name, image),
                    count,
                    get_card_links(card, english_card, locale),
                )
            )

        total_dust = sum(card.crafting_costs[0] * count for card, count in cards)

        table = tabulate(rows, headers=("Mana", "Card Name", "Qty", "Links"))
        reply_chunks.append(table)

        reply_chunks.append("\n")
        reply_chunks.append(f"**Total Dust:** {total_dust}")
        reply_chunks.append("\n")

        reply_chunks.append(f"**Deck Code:** {deck.as_deckstring}")
        reply_chunks.append("\n")
        reply_chunks.append("*****")
        reply_chunks.append("\n")

        if calculate_reply_length(reply + reply_chunks) > MAX_CHARACTERS:
            # Stop adding decks
            break

        reply += reply_chunks

    reply.append(I_AM_A_BOT)
    return "\n".join(reply)


def get_card_links(card, english_card, locale):
    hsreplaynet_link = get_hsreplaynet_link(card, locale)
    gamepedia_link = get_gamepedia_link(english_card)

    return ",".join(
        (
            markdown_link("HSReplay", hsreplaynet_link),
            markdown_link("Wiki", gamepedia_link),
        )
    )


def get_hsreplaynet_link(card, locale):
    ret = f"https://hsreplay.net/cards/{card.dbf_id}/"
    if locale != "enUS":
        locale = {
            "esMX": "es-mx",
            "ptBR": "pt-br",
            "zhCN": "zh-hans",
            "zhTW": "zh-hant",
        }.get(
            locale, locale[:2]
        )  # pull first two characters by default
        ret += f"?hl={locale}"

    return ret


def get_gamepedia_link(card):
    return f"https://hearthstone.gamepedia.com/{quote(card.name)}"


def get_card_image(card, locale):
    return (
        f"https://art.hearthstonejson.com/v1/render/latest/{locale}/512x/{card.id}.png"
    )
