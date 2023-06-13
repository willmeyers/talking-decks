import os
import sys
import json
import random
import logging
import asyncio
import pathlib
import tomllib
import hashlib
import argparse

import aiohttp
import aiofiles
import genanki

from talking_decks.deck_model import MODEL


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# Play.ht Setup
#
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
if not PLAYHT_API_KEY:
    raise ValueError("PLAYHT_API_KEY is not set")


PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
if not PLAYHT_USER_ID:
    raise ValueError("PLAYHT_USER_ID is not set")


BASE_API_URL = "https://play.ht/api/v1"


REQUEST_HEADERS = {
    "accept": "text/event-stream",
    "content-type": "application/json",
    "authorization": f"Bearer {PLAYHT_API_KEY}",
    "x-user-id": PLAYHT_USER_ID,
}


class Notes:
    def __init__(self, deck_dir, data, voices):
        self.deck_dir = deck_dir
        self.data = data
        self.voices = voices
        self.http_session = aiohttp.ClientSession(headers=REQUEST_HEADERS)

    def __aiter__(self):
        return self

    async def transcribe(self, question, voice):
        payload = {"content": [question], "voice": voice}
        async with self.http_session.post(
            f"{BASE_API_URL}/convert", json=payload
        ) as resp:
            if not resp.ok:
                logger.error(
                    f"transcribe: Status code: {resp.status} for content: {question}. {await resp.text()}"
                )
                return None

            transcription = await resp.json()
            task_id: str = transcription.get("transcriptionId", None)
            if not task_id:
                logger.error(
                    f"transcribe: No transcriptionId for content: {question}. {await resp.text()}"
                )
                return None

            return task_id

    async def download_media(self, task_id, filename):
        converted_transcription = None
        elapsed = 0
        complete = False

        while not complete:
            if elapsed > 10:
                logger.error(f"download_media: Timeout for task_id: {task_id}")
                return None

            await asyncio.sleep(1)
            elapsed += 1
            async with self.http_session.get(
                f"{BASE_API_URL}/articleStatus?transcriptionId={task_id}"
            ) as resp:
                if resp.status != 200:
                    logger.error(
                        f"download_media: Status code: {resp.status} for task_id: {task_id}. {await resp.text()}"
                    )
                    return None

                converted_transcription = await resp.json()
                complete = converted_transcription.get("converted", False) == True

        media_url = converted_transcription.get("audioUrl")
        if not media_url:
            logger.error(
                f"download_media: No audioUrl for task_id: {task_id}. {await resp.text()}"
            )
            return None

        # Create a new session to download the media file as the previous session contains auth headers
        # which block the file from being downloaded.
        async with aiohttp.ClientSession() as temp_session:
            async with temp_session.get(media_url) as resp:
                if resp.status != 200:
                    logger.error(
                        f"download_media: Status code: {resp.status} for media_url: {media_url}. {await resp.text()}"
                    )
                    return None

                media = await resp.read()

                media_file = pathlib.Path(f"{self.deck_dir}/media/{filename}.mp3")
                media_file.parent.mkdir(parents=True, exist_ok=True)
                media_filename = media_file.name
                fo = await aiofiles.open(media_file, mode="wb")
                await fo.write(media)
                await fo.close()

            await temp_session.close()

        return media_filename

    async def __anext__(self):
        if not self.data:
            await self.http_session.close()
            raise StopAsyncIteration

        item = self.data.pop(0)

        question = item["Question"]
        voice = item.get("Voice", "X")

        if not voice or voice == "X":
            voice = random.choice(self.voices["male"] + self.voices["female"])
        elif voice == "M":
            voice = random.choice(self.voices["male"])
        elif voice == "F":
            voice = random.choice(self.voices["female"])

        if not voice:
            self.http_session.close()
            raise StopAsyncIteration(f"A voice could not be found for: {question}")

        task_id = await self.transcribe(question=question, voice=voice)
        media = None
        if task_id:
            media_hash = hashlib.md5(item["Question"].encode("utf-8")).hexdigest()
            media = await self.download_media(
                task_id=task_id, filename=media_hash
            )

        note_fields = [item["Question"], item["Answer"]]
        if media:
            note_fields.append(f"[sound:{media}]")
        else:
            logger.warning(f"No media will be added to note: {item['Question']}")

        note = genanki.Note(
            model=MODEL,
            fields=note_fields,
        )

        return note


async def make_deck():
    parser = argparse.ArgumentParser(
        description="talking-decks: Build a deck of annotated notes for Anki"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="The target deck directory. Ex. 'en_fr/common_phrases_a1_a2'",
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

    # Read the input file
    with open(deck_dir / args.notes_file, "r") as f:
        data = json.load(f)

    # Initialize media directory
    media_dir = deck_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # Load toml
    with open(deck_dir / "deck.toml", "rb") as f:
        config = tomllib.load(f)

    deck_name = config["deck"]["name"]
    voices = config["voices"]

    # # Create the deck
    deck = genanki.Deck(
        random.randrange(1 << 30, 1 << 31),
        deck_name,
    )

    notes = Notes(deck_dir=deck_dir, data=data, voices=voices)

    async for note in notes:
        deck.add_note(note=note)
        logger.info(f"Added note: {note.fields[0]}")
        logger.debug(f"Note: {note}")

    media_files = []
    if (deck_dir / "media").exists():
        media_files = os.listdir(deck_dir / "media")
        media_files = [f"{media_dir}/{f}" for f in media_files]

    logger.info(f"Writing deck...")
    genanki.Package(deck, media_files=media_files).write_to_file(
        f"{deck_dir}/{deck_name}.apkg"
    )

    logger.info("Done!")


def main():
    asyncio.run(make_deck())


if __name__ == "__main__":
    main()
