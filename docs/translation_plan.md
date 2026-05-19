# DeepRenPyTrans: Translation Plan

## Overview

DeepRenPyTrans uses a **dictionary-based runtime injection** approach to translate Ren'Py games without modifying source code.

## Pipeline

### 1. Extraction (`extract`)
- **Method**: Regex-based greedy extraction from all `.rpy` files
- **Context Mapping**: Strings are grouped by source file for LLM context
- **Smart Filters**: Configurable `TranslatableFilter` class skips:
  - Internal IDs (prefixed: `ITM*`, `ACT*`, `LOC*`, etc.)
  - Python code, assertions, docstrings
  - File paths, hex colors, pure variables
  - Debug/logging messages
  - Already-translated text (Cyrillic/CJK detection)

### 2. Translation (`translate`)
- **Providers**: DeepSeek V3, OpenAI GPT-4, local Ollama
- **Smart Batching**: Strings sent file-by-file (40-50 per batch) for scene context
- **Protection**: System prompt preserves `[variable]` and `{tag}` syntax
- **Incremental**: Skips already-translated keys, resumes on crash
- **Rate Limiting**: Configurable delay between batches

### 3. Injection (`inject`)
- **File**: `game/tl/<lang>/hooks.rpy`
- **Method**: `config.replace_text` + `config.say_menu_text_filter`
- **Ren'Py 8**: Python 3 compatible (`str` not `basestring`)
- **Auto-Switch**: Sets language on first run via `persistent`
- **Live Toggle**: Configurable hotkey for instant language switching
- **Logging**: Untranslated strings auto-logged to `untranslated.log`

### 4. Quality Control (`audit` + `clean`)
- **Untranslated Logger**: Runtime log → targeted translation passes
- **Audit Report**: Finds untranslated, orphaned, identical, empty, and junk entries
- **Dictionary Cleanup**: Removes debug strings, code conditions, docstrings
- **Dry Run**: Preview changes before applying

## Deployment

### PC
1. Copy `game/tl/<lang>/` folder to target game
2. Run the game

### Android (APK Injection)
1. Unpack APK as ZIP
2. Inject `tl/<lang>/` into `assets/x-game/` or `assets/game/`
3. Repack and sign with `apksigner`

### iOS
1. Generate Xcode project from Ren'Py Launcher
2. Inject translation files
3. Build and deploy
