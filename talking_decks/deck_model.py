import random
import genanki

FIELDS = [{"name": "Question"}, {"name": "Answer"}, {"name": "MyMedia"}]

TEMPLATES = [
    {
        "name": "bigdecks",
        "qfmt": "{{MyMedia}}<br>{{Question}}",
        "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
    }
]

MODEL = genanki.Model(
    random.randrange(1 << 30, 1 << 31),
    "Simple Model",
    fields=FIELDS,
    templates=TEMPLATES,
)
