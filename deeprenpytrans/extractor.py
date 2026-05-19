"""
Universal string extractor for Ren'Py games.
Walks .rpy files, extracts all quoted strings, and filters them for translatability.
"""

import os
import re
import json
from .filters import TranslatableFilter


# Regex to find all double-quoted strings (handles escaped quotes)
STRING_PATTERN = re.compile(r'"(.*?)(?<!\\)"')


def extract_strings(
    game_dir: str,
    output_path: str = None,
    filter_config: dict = None,
    include_log: str = None,
    verbose: bool = False,
) -> dict:
    """
    Extract all translatable strings from .rpy files in game_dir.

    Args:
        game_dir: Path to the game/ directory containing .rpy files.
        output_path: Optional path to write strings_by_file.json.
        filter_config: Dict with filter settings (skip_prefixes, force_include, etc.)
        include_log: Optional path to untranslated.log to merge into results.
        verbose: Print detailed progress.

    Returns:
        Dict mapping relative file paths to lists of translatable strings.
    """
    fc = filter_config or {}
    tf = TranslatableFilter(
        skip_prefixes=fc.get("skip_prefixes"),
        force_include=fc.get("force_include"),
        force_exclude=fc.get("force_exclude"),
        min_length=fc.get("min_length", 2),
    )

    file_map = {}
    total_strings = 0
    skipped_strings = 0

    for root, dirs, files in os.walk(game_dir):
        # Skip translation directories to avoid extracting translated strings
        dirs[:] = [d for d in dirs if d != "tl"]

        for filename in sorted(files):
            if not filename.endswith(".rpy"):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, game_dir)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, IOError) as e:
                if verbose:
                    print(f"  ⚠ Error reading {rel_path}: {e}")
                continue

            matches = STRING_PATTERN.findall(content)
            unique_in_file = []
            seen = set()

            for match in matches:
                clean_str = match.replace('\\"', '"')
                if clean_str in seen:
                    continue
                seen.add(clean_str)

                if tf.is_translatable(clean_str):
                    unique_in_file.append(clean_str)
                else:
                    skipped_strings += 1

            if unique_in_file:
                file_map[rel_path] = unique_in_file
                total_strings += len(unique_in_file)

            if verbose and unique_in_file:
                print(f"  📄 {rel_path}: {len(unique_in_file)} strings")

    # Merge untranslated.log if provided
    if include_log and os.path.exists(include_log):
        log_strings = _parse_untranslated_log(include_log, tf)
        if log_strings:
            existing = set()
            for strings in file_map.values():
                existing.update(strings)

            new_from_log = [s for s in log_strings if s not in existing]
            if new_from_log:
                file_map["__untranslated_log__"] = new_from_log
                total_strings += len(new_from_log)
                if verbose:
                    print(f"  📋 untranslated.log: {len(new_from_log)} new strings")

    if verbose:
        print(f"\n✅ Extracted {total_strings} strings from {len(file_map)} sources")
        print(f"   Skipped {skipped_strings} non-translatable strings")

    # Write output
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(file_map, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"   Saved to {output_path}")

    return file_map


def _parse_untranslated_log(log_path: str, tf: TranslatableFilter) -> list:
    """Parse untranslated.log and return valid strings."""
    with open(log_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Deduplicate while preserving order
    seen = set()
    result = []
    for line in lines:
        if line not in seen and len(line) > 1:
            seen.add(line)
            result.append(line)

    return result
