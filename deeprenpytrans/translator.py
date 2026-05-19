"""
Multi-provider AI translation pipeline for Ren'Py games.
Supports DeepSeek, OpenAI, and local Ollama models.
"""

import json
import os
import time
import requests
from tqdm import tqdm


def build_system_prompt(target_language: str) -> str:
    """Build the system prompt for the translation LLM."""
    return f"""You are a professional game translator. You are translating a Ren'Py visual novel game into {target_language}.
I will provide you with a list of strings from a SINGLE script file (one scene/chapter).
Use the sequence of strings to understand the context, characters, and tone of the scene.
Rules:
1. Preserve ALL Ren'Py tags like {{b}}, {{i}}, {{a=...}}, {{/a}}, {{color=...}}, etc. exactly as-is.
2. Preserve ALL variables in brackets like [player_name], [GAME.mc.name], etc. exactly as-is.
3. Return ONLY a valid JSON object where keys are original strings and values are translations.
4. Maintain consistency: if a character name or technical term appears multiple times, translate it consistently.
5. If a string is clearly an internal ID, code snippet, or file path, return it unchanged as the value.
6. For proper nouns (character names, place names), transliterate them consistently.
7. Keep the same formatting: if the original has \\n, keep \\n. If it has trailing spaces, keep them.
"""


def translate_batch(
    batch: list,
    context_info: str,
    api_key: str,
    base_url: str,
    model: str,
    target_language: str,
    temperature: float = 0.2,
    max_retries: int = 3,
) -> dict:
    """
    Send a batch of strings to the AI API for translation.
    Returns a dict mapping original → translated strings.
    """
    system_prompt = build_system_prompt(target_language)
    input_dict = {s: "" for s in batch}
    user_content = f"Context: {context_info}\nStrings to translate:\n{json.dumps(input_dict, ensure_ascii=False)}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for attempt in range(max_retries):
        try:
            response = requests.post(
                base_url, json=payload, headers=headers, timeout=120
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Clean markdown formatting sometimes returned by models
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait = min(30, 5 * (attempt + 1))
                print(f"  ⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  ❌ HTTP error: {e}")
                time.sleep(3)
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {e}. Retrying ({attempt + 1}/{max_retries})...")
            time.sleep(3)

    return {}


def translate(
    strings_path: str,
    dict_path: str,
    config: dict,
    verbose: bool = False,
) -> dict:
    """
    Main translation pipeline. Reads extracted strings, translates missing ones
    via AI, and incrementally saves to the dictionary file.

    Args:
        strings_path: Path to strings_by_file.json (from extractor).
        dict_path: Path to dictionary.json (output/incremental).
        config: Full config dict (from config.py).
        verbose: Print progress info.

    Returns:
        The final translations dict.
    """
    api_config = config["api"]
    api_key = api_config.get("api_key", "")
    base_url = api_config["base_url"]
    model = api_config["model"]
    target_language = config["target_language"]
    temperature = api_config.get("temperature", 0.2)
    batch_size = api_config.get("batch_size", 40)
    max_retries = api_config.get("max_retries", 3)
    delay = api_config.get("delay", 1.0)

    # Load existing translations
    translations = {}
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        if verbose:
            print(f"📖 Loaded {len(translations)} existing translations")

    # Load source strings
    with open(strings_path, "r", encoding="utf-8") as f:
        file_map = json.load(f)

    # Count total work
    total_new = sum(
        1 for strings in file_map.values()
        for s in strings if s not in translations
    )

    if total_new == 0:
        if verbose:
            print("✅ All strings are already translated!")
        return translations

    if verbose:
        print(f"🔄 {total_new} strings need translation across {len(file_map)} files\n")

    # Progress bar
    pbar = tqdm(total=total_new, desc="Translating", unit="str", disable=not verbose)

    for file_key, file_strings in file_map.items():
        to_translate = [s for s in file_strings if s not in translations]

        if not to_translate:
            continue

        context = f"File: {file_key}" if file_key != "__untranslated_log__" else "UI and runtime-logged strings"

        for i in range(0, len(to_translate), batch_size):
            batch = to_translate[i : i + batch_size]

            result = translate_batch(
                batch=batch,
                context_info=context,
                api_key=api_key,
                base_url=base_url,
                model=model,
                target_language=target_language,
                temperature=temperature,
                max_retries=max_retries,
            )

            if result:
                translations.update(result)
                # Incremental save after each batch
                _save_dict(translations, dict_path)
                pbar.update(len(result))
            else:
                pbar.update(len(batch))  # Still advance on failure

            time.sleep(delay)

    pbar.close()

    if verbose:
        print(f"\n✅ Translation complete! Dictionary: {len(translations)} entries")

    return translations


def _save_dict(translations: dict, path: str):
    """Atomically save translations dict to JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    # Atomic rename
    if os.path.exists(path):
        os.replace(tmp_path, path)
    else:
        os.rename(tmp_path, path)
