import json
import hashlib
import pathlib
from unittest import TestCase


class TestDecks(TestCase):
    def test_decks(self):
        decks_dir = pathlib.Path(__file__).parent.parent.parent / "decks"

        for deck_dir in decks_dir.iterdir():
            if deck_dir.is_dir():
                for deck_category in deck_dir.iterdir():
                    if deck_category.is_dir():
                        for deck in deck_category.iterdir():
                            if deck.is_dir():
                                current_working_deck = deck_dir / deck_category.name 
                                deck_media_dir = current_working_deck / "media"
                                deck_notes_json = current_working_deck / "notes.json"
                                with open(deck_notes_json) as f:
                                    deck_notes = json.load(f)

                                for note in deck_notes:
                                    question = note["Question"]
                                    field_hash = hashlib.md5(question.encode("utf-8")).hexdigest()
                                    field_file = deck_media_dir / f"{field_hash}.mp3"
                                    self.assertTrue(field_file.exists())
