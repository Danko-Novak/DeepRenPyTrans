# 🎮 DeepRenPyTrans

**AI-powered universal translator for Ren'Py visual novel games.**

🌐 [English](README.md) | [Русский](README.ru.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [简体中文](README.zh.md)

---

Translate any Ren'Py game into any language using DeepSeek (including deepseek-v4-flash / deepseek-v4-pro), OpenAI, or local LLMs — without touching the game's source code.

---

## ✨ Features

- **🔍 Smart Extraction** — Automatically finds all translatable strings in `.rpy` files, filtering out code, IDs, and debug messages
- **🤖 AI Translation** — Batch translation via DeepSeek, OpenAI, or local Ollama with scene-aware context
- **🔌 Runtime Injection** — Zero-modification hook system using Ren'Py's built-in `config.replace_text`
- **📊 Quality Audit** — Find untranslated strings, orphaned translations, and junk entries
- **🧹 Dictionary Cleanup** — Automatically remove debug strings, docstrings, and code artifacts
- **⚡ Incremental** — Resume interrupted translations, only process new/missing strings
- **📱 Cross-platform** — Works with PC, Android (APK injection), and iOS builds

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/Danko-Novak/DeepRenPyTrans.git
cd DeepRenPyTrans

# Option A: Install as a package (recommended — gives you the `deeprenpytrans` command)
pip install -e .

# Option B: Just install dependencies
pip install -r requirements.txt
```

> After `pip install -e .` you can use `deeprenpytrans` directly instead of `python -m deeprenpytrans`.

### 2. Configure

```bash
# Copy example configs
cp .env.example .env
cp config.example.yaml config.yaml

# Edit .env with your API key
# Edit config.yaml with your game path and target language
```

You can run the tool in two ways:

#### Option A: Web Console GUI (Recommended)
You can start the console in two ways:
- Simply double-click the `run_gui.bat` file in the project's root folder.
- Or execute manually in your terminal:
  ```bash
  python gui_server.py
  ```
This automatically opens your browser at `http://localhost:8000`.

#### Option B: Command Line Interface (CLI)

```bash
# Step 1: Extract strings from your game
python -m deeprenpytrans extract --game "./MyGame/game"

# Step 2: Translate with AI
python -m deeprenpytrans translate --strings strings_by_file.json --dict "./MyGame/game/tl/russian/dictionary.json"

# Step 3: Generate runtime hooks
python -m deeprenpytrans inject --game "./MyGame/game" --lang russian
```


## 📖 Commands

### `extract` — Find translatable strings

```bash
python -m deeprenpytrans extract --game ./MyGame/game --output strings.json
```

Walks all `.rpy` files, extracts quoted strings, and applies smart filters to skip:
- Internal IDs (`ITM_Sword`, `LOC_Bridge`, `ACT_NPC01`)
- Python code and assertions
- File paths and hex colors
- Debug/logging messages
- Already-translated text (Cyrillic detection)

Options:
| Flag | Description |
|------|-------------|
| `--game PATH` | Path to the `game/` directory |
| `--output FILE` | Output JSON file (default: `strings_by_file.json`) |
| `--include-log PATH` | Merge strings from `untranslated.log` |

### `translate` — AI-powered translation

```bash
python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
```

Sends strings to the AI in smart batches (grouped by source file for context).
Supports incremental translation — already-translated strings are skipped.

### `audit` — Quality check

```bash
python -m deeprenpytrans audit --dict dictionary.json --strings strings.json
```

Produces a report showing:
- ❌ Untranslated strings (in source, not in dictionary)
- 👻 Orphaned translations (in dictionary, not in source)
- 🔁 Identical key=value pairs (possibly not translated)
- 📭 Empty translations
- 🗑️ Junk entries (debug messages, code snippets)

### `clean` — Remove junk from dictionary

```bash
python -m deeprenpytrans clean --dict dictionary.json --dry-run
python -m deeprenpytrans clean --dict dictionary.json --remove-orphaned
```

Options:
| Flag | Description |
|------|-------------|
| `--dry-run` | Preview what would be removed |
| `--keep-junk` | Don't remove debug/code strings |
| `--remove-orphaned` | Also remove strings not found in source |

### `inject` — Generate hooks.rpy

```bash
python -m deeprenpytrans inject --game ./MyGame/game --lang russian
```

Generates a `hooks.rpy` file that:
- Loads `dictionary.json` at runtime
- Intercepts all text via `config.replace_text`
- Logs untranslated strings to `untranslated.log`
- Adds a hotkey to toggle translation on/off
- Overrides fonts for the target language

## ⚙️ Configuration

### `config.yaml`

```yaml
game_dir: "./MyGame/game"
target_language: "Russian"
translation_dir: "russian"

api:
  provider: "deepseek"    # or "openai", "ollama"
  model: "deepseek-chat"
  temperature: 0.2
  batch_size: 40

fonts:
  default: "DejaVuSans.ttf"
  replacements:
    "OriginalFont.ttf": "DejaVuSans.ttf"

extraction:
  skip_prefixes: ["ITM", "ACT", "LOC", "QST"]
  force_include: ["Q.Save", "Q.Load"]
```

### `.env`

```bash
DEEPSEEK_API_KEY=sk-your-key-here
# or
OPENAI_API_KEY=sk-your-openai-key
```

## 🏗️ How It Works

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  .rpy files │────▶│  Extractor   │────▶│ strings.json   │
│  (game src) │     │  (filters)   │     │ (by file)      │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│ dictionary  │◀────│  Translator  │◀────│  AI Provider   │
│   .json     │     │  (batches)   │     │ (DeepSeek/etc) │
└──────┬──────┘     └──────────────┘     └────────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  hooks.rpy  │────▶│  Ren'Py Game │ ← Player sees translated text!
│  (runtime)  │     │  (runtime)   │
└─────────────┘     └──────────────┘
```

## 📱 Mobile Deployment

### Android (APK Injection)
1. Use our automated script `build_apk.bat` which handles everything:
   - Extracting game assets from the old APK.
   - Restoring compressed assets from the old APK to save up to 60% of size (averaging ~400-500MB savings).
   - Performing wav-to-ogg audio compression.
   - Optimizing new images for mobile while skipping already compressed assets.
   - Repacking the APK using ultra-compression and signing it automatically.
2. **Customization**: You can customize the build process by editing the flags at the top of `build_apk.bat`:
   - `RESTORE_OLD_ASSETS` (1/0): Enable/disable restoring already compressed assets from the old APK.
   - `COMPRESS_AUDIO` (1/0): Enable/disable wav-to-ogg conversion and script patching.
   - `COMPRESS_IMAGES` (1/0): Enable/disable mobile image compression.
   - `INJECT_TRANSLATION` (1/0): Enable/disable translation injection. Set to `0` to build a clean untranslated port.
   - `LANG_FOLDER`: Folder name of your target language inside `game/tl/` (e.g., `russian`).
   - `COMPRESSION_LEVEL` (0-9): Adjust the 7-Zip compression level (9 = ultra compression, 0 = store).
3. If building manually, unpack the APK, replace assets inside `assets/x-game/game/`, clean `META-INF/` signatures, and repack/sign.

### iOS
1. Generate Xcode project from Ren'Py Launcher
2. Add `tl/russian/` to the project
3. Build and deploy
## ⚠️ Important Note & Limitations

- **Testing Status**: This tool has been tested and verified on a single game so far, where everything was translated and built correctly.
- **Game-Specific Code**: While the goal was to create a perfect universal translation tool, other Ren'Py games might (and likely will) require some adjustments to accommodate their specific codebase, custom prefixes, or scripting quirks.
- **No Coding Skills?**: If you don't know how to code or don't have the time to modify the scripts, we highly recommend using AI coding assistants like **Antigravity**, **Cursor**, or similar tools to help you adapt the extractor and filters for your target game.

## 🤝 Contributing

PRs welcome! Areas that need help:
- Additional LLM provider integrations
- CJK language support and testing
- Improved extraction heuristics for specific games

## 🗺️ Roadmap & Features

We track our development, plan new features, and prioritize tasks based on community feedback. If you have an idea or want to request a feature, please go to the **Discussions** tab on GitHub, submit your proposal, or upvote existing ideas!

| Feature | Votes | Status | Progress |
| :--- | :--- | :--- | :--- |
| **GUI Web Console (Dashboard)** | - | 🚀 Released | `[████████████████████]` 100% |
| **Android APK Packer & Optimizer** | - | 🚀 Released | `[████████████████████]` 100% |
| **Local LLMs & Ollama Support** | - | 🚀 Released | `[████████████████████]` 100% |
| **macOS & Linux Support** | 0 | 📋 Planned | `[██░░░░░░░░░░░░░░░░░░]` 10% |
| **Japanese/Chinese Translation Audits** | 0 | 📋 Planned | `[█░░░░░░░░░░░░░░░░░░░]` 5% |

---

## 💖 Support the Project

DeepRenPyTrans is a passion project built to streamline the VN translation process. If this tool has saved you time or helped you bring a game to a new audience, consider supporting its development.

I am currently running a budget development station and aiming to upgrade it to a dedicated local AI workstation running Linux with ROCm. This will allow native, high-speed testing of local LLMs.

**Current Fund Target:** 0 / 1,200 USD

### 🚀 Upgrade Tiers:
* **Tier 1: GPU Upgrade ($850)** — Upgrade to a 24GB AMD Radeon GPU (e.g., RX 7900 XTX or next-gen equivalent) for running large local LLMs (like 14B/32B/70B models) locally under Linux ROCm.
* **Tier 2: Storage Upgrade ($150)** — Upgrade to a fast 2TB PCIe 4.0 NVMe SSD. Local LLM models require huge disk space (5GB to 40GB+ per model), and my current 500GB SSD is full.
* **Tier 3: RAM Upgrade ($150)** — Add another 32GB of RAM (upgrading to 64GB total) to allow parallel workflows, heavy IDE multitasking, and CPU-offloading for extra large models.
* **Ongoing: API Fund ($50)** — Small budget for testing commercial APIs (DeepSeek, OpenAI, Claude) during translation testing.

### How to help:
* **Star the repo:** It helps with visibility and motivates me to keep coding!
* **Contribute:** Open issues, suggest features, or submit PRs.
* **Donate (USDT - TON / TON Network):**
  `UQBdHUyR8nG5p_Rwhw_Rtmgc7QJdJ-G5nOPJa7Pq0mh2A27K`

## 📄 License

GNU AGPL v3 — see [LICENSE](LICENSE).
