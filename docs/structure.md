# DeepRenPyTrans: Project Structure

## 📦 Package (`deeprenpytrans/`)

| File | Role | Description |
|------|------|-------------|
| `__init__.py` | 🏷️ Version | Package metadata |
| `__main__.py` | 🚪 Entry | `python -m deeprenpytrans` support |
| `cli.py` | 🖥️ CLI | argparse subcommands: extract, translate, audit, clean, inject |
| `config.py` | ⚙️ Config | YAML + .env loader with defaults and provider mapping |
| `filters.py` | 🧠 Brain | `TranslatableFilter` class — decides what to translate vs skip |
| `extractor.py` | ⛏️ Miner | Walks .rpy files, extracts quoted strings, applies filters |
| `translator.py` | ✍️ Scribe | Multi-provider AI translation with batching and progress |
| `auditor.py` | 🔍 Inspector | Finds untranslated, orphaned, junk, and empty entries |
| `hooks_generator.py` | 🔌 Injector | Generates hooks.rpy for runtime text replacement |

## 📄 Root Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation with usage examples |
| `LICENSE` | MIT License |
| `requirements.txt` | Python dependencies |
| `config.example.yaml` | Example configuration (copy to `config.yaml`) |
| `.env.example` | Example API keys (copy to `.env`) |
| `.gitignore` | Git exclusion rules |

## 🎮 Game Output (generated per-game)

| File | Location | Description |
|------|----------|-------------|
| `hooks.rpy` | `game/tl/<lang>/` | Runtime translation injection hooks |
| `dictionary.json` | `game/tl/<lang>/` | JSON key-value translation dictionary |
| `untranslated.log` | `game/` | Auto-logged missing strings (runtime) |
| `strings_by_file.json` | working dir | Extracted strings grouped by source file |
