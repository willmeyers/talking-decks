import os
import sys
import json
import random
import logging
import pathlib
import hashlib
import tomllib
import argparse

import genanki

from talking_decks.deck_model import MODEL


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def build_deck():
    parser = argparse.ArgumentParser(
        description="talking-decks: Build a deck of annotated notes for Anki"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="The target deck directory",
        required=True,
    )

    parser.add_argument(
        "--notes-file",
        type=str,
        help="The input file containing the flashcards",
        default="notes.json",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        help="The log level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()

    logger.setLevel(args.log_level)

    # Get target directory
    deck_dir = pathlib.Path("decks/" + args.target)
    if not deck_dir.exists():
        logger.error(f"Target deck directory: {deck_dir} does not exist")
        sys.exit(1)

    media_dir = deck_dir / "media"

    # Read the input file
    with open(deck_dir / args.notes_file, "r") as f:
        data = json.load(f)

    # Load toml
    with open(deck_dir / "deck.toml", "rb") as f:
        config = tomllib.load(f)

    deck_name = config["deck"]["name"]

    # Create the deck
    deck = genanki.Deck(
        random.randrange(1 << 30, 1 << 31),
        deck_name,
    )

    for item in data:
        media_hash = hashlib.md5(item["Question"].encode("utf-8")).hexdigest()
        media_filename = media_hash + ".mp3"
        media = media_filename

        note = genanki.Note(
            model=MODEL,
            fields=[item["Question"], item["Answer"], f"[sound:{media}]"],
        )
        deck.add_note(note)

        logger.info(f"Added note: {item['Question']}")

    media_files = os.listdir(media_dir)
    media_files = [f"{media_dir}/{f}" for f in media_files]

    # Create the package
    logger.info("Writing deck...")
    genanki.Package(deck, media_files=media_files).write_to_file(
        f"{deck_dir}/{deck_name}.apkg"
    )

    logger.info("Done!")


def main():
    build_deck()


if __name__ == "__main__":
    main()
