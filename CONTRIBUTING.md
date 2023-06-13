# Contributing

Thanks for your interest in contributing

## Setting Up

Once you've cloned the repo, you can install the dependencies with [Poetry](https://python-poetry.org/):

```
poetry install
```

You'll also need to set up a [Play.ht](https://play.ht/) account if you want to make decks.
Once you've created an account, you can complete the setup by running:

```bash
export PLAYHT_API_KEY=<your_api_key>
export PLAYHT_USER_ID=<your_user_id>
```

Now that you're set up, feel free to start messing around! Add notes, tweak pronunciations, and maybe be inspired to pick up a new language.

## Making a New Deck

Create or find an existing directory in the `decks` directory for your language. The name of the directory should follow the format
`<source_language>_<target_language>/<deck_name>`. For example, `en_fr/common_phrases_a1_a2`.

Inside the directory, create a file called `deck.toml`. This file should contain the following:

```toml
[deck]
name = "Deck Name"

[voices]
male = [...]
female = [...]
```

Create a `notes.json` file and start adding notes. The format of the notes should be:

```json
[
    {"Question": "Hola", "Answer": "Hello"},
    {"Question": "Adiós", "Answer": "Goodbye"},
    ...
]
```

you can add an optional `Voice` key to each item to specify the program to sample from the male (`M`) or female (`F`) voices, or select no preference (`X`). For example:

```json
[
    {"Question": "Hola", "Answer": "Hello", "Voice": "M"},
    {"Question": "Adiós", "Answer": "Goodbye", "Voice": "F"},
    {"Question": "¿Cómo estás?", "Answer": "How are you?", "Voice": "X"}
    ...
]
```

Once your Play.ht account is set up, you can run

```bash
poetry run make_deck --target <path_to_deck_directory>
```

## Building an Existing Deck

You can quickly build an existing deck by running:

```bash
poetry run build_deck --target <path_to_deck_directory>
```

## Testing

You can run the tests with:

```bash
poetry run pytest
```
