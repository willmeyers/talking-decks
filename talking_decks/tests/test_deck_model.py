from unittest import TestCase


class TestDeckModel(TestCase):
    def test_deck_model(self):
        from talking_decks.deck_model import MODEL
        import genanki

        # Sanity check...
        self.assertTrue(isinstance(MODEL, genanki.Model))
