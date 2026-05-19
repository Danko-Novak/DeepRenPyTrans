"""
Translation dictionary auditor.
Finds untranslated strings, orphaned translations, junk entries, and inconsistencies.
"""

import json
import os
from .filters import TranslatableFilter


def audit(
    dict_path: str,
    strings_path: str = None,
    filter_config: dict = None,
    verbose: bool = False,
) -> dict:
    """
    Audit a translation dictionary for quality issues.

    Args:
        dict_path: Path to dictionary.json.
        strings_path: Optional path to strings_by_file.json for cross-referencing.
        filter_config: Filter settings for junk detection.
        verbose: Print findings to console.

    Returns:
        Dict with audit results:
        {
            "untranslated": [...],     # In source but not in dict
            "orphaned": [...],         # In dict but not in source
            "identical": [...],        # key == value (possibly untranslated)
            "empty": [...],            # value is empty string
            "junk": [...],             # Debug/code strings that don't belong
            "stats": {...}             # Summary statistics
        }
    """
    fc = filter_config or {}
    tf = TranslatableFilter(
        skip_prefixes=fc.get("skip_prefixes"),
        force_include=fc.get("force_include"),
        force_exclude=fc.get("force_exclude"),
    )

    # Load dictionary
    with open(dict_path, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    # Load source strings if available
    source_strings = set()
    if strings_path and os.path.exists(strings_path):
        with open(strings_path, "r", encoding="utf-8") as f:
            file_map = json.load(f)
        for strings in file_map.values():
            source_strings.update(strings)

    results = {
        "untranslated": [],
        "orphaned": [],
        "identical": [],
        "empty": [],
        "junk": [],
    }

    # 1. Find untranslated: in source but not in dict
    if source_strings:
        for s in sorted(source_strings):
            if s not in dictionary:
                results["untranslated"].append(s)

    # 2. Find orphaned: in dict but not in source
    if source_strings:
        for key in dictionary:
            if key not in source_strings:
                results["orphaned"].append(key)

    # 3. Find identical key=value pairs (possibly untranslated)
    for key, value in dictionary.items():
        if key == value and len(key.strip()) > 1:
            results["identical"].append(key)

    # 4. Find empty translations
    for key, value in dictionary.items():
        if value == "" and len(key.strip()) > 1:
            results["empty"].append(key)

    # 5. Find junk entries
    for key, value in dictionary.items():
        if tf.is_junk(key, value):
            results["junk"].append(key)

    # Stats
    results["stats"] = {
        "total_entries": len(dictionary),
        "source_strings": len(source_strings),
        "untranslated_count": len(results["untranslated"]),
        "orphaned_count": len(results["orphaned"]),
        "identical_count": len(results["identical"]),
        "empty_count": len(results["empty"]),
        "junk_count": len(results["junk"]),
    }

    if verbose:
        _print_report(results)

    return results


def clean_dictionary(
    dict_path: str,
    strings_path: str = None,
    filter_config: dict = None,
    remove_junk: bool = True,
    remove_orphaned: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Clean a translation dictionary by removing junk and/or orphaned entries.

    Args:
        dict_path: Path to dictionary.json.
        strings_path: Path to strings_by_file.json for orphan detection.
        filter_config: Filter settings.
        remove_junk: Remove debug/code strings.
        remove_orphaned: Remove strings not found in source files.
        dry_run: Only report what would be removed, don't actually modify.
        verbose: Print progress.

    Returns:
        Dict with removed entries for review.
    """
    fc = filter_config or {}
    tf = TranslatableFilter(
        skip_prefixes=fc.get("skip_prefixes"),
        force_include=fc.get("force_include"),
        force_exclude=fc.get("force_exclude"),
    )

    with open(dict_path, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    source_strings = set()
    if strings_path and os.path.exists(strings_path):
        with open(strings_path, "r", encoding="utf-8") as f:
            file_map = json.load(f)
        for strings in file_map.values():
            source_strings.update(strings)

    to_remove = set()

    if remove_junk:
        for key, value in dictionary.items():
            if tf.is_junk(key, value):
                to_remove.add(key)

    if remove_orphaned and source_strings:
        for key in dictionary:
            if key not in source_strings:
                to_remove.add(key)

    removed = {k: dictionary[k] for k in to_remove if k in dictionary}

    if verbose:
        action = "Would remove" if dry_run else "Removing"
        print(f"🧹 {action} {len(removed)} entries from dictionary")
        for k in list(removed.keys())[:20]:
            print(f"   - {k[:80]}...")
        if len(removed) > 20:
            print(f"   ... and {len(removed) - 20} more")

    if not dry_run and removed:
        cleaned = {k: v for k, v in dictionary.items() if k not in to_remove}
        with open(dict_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"✅ Cleaned dictionary: {len(dictionary)} → {len(cleaned)} entries")

    return removed


def _print_report(results: dict):
    """Print a human-readable audit report."""
    stats = results["stats"]

    print("=" * 60)
    print("📊 TRANSLATION AUDIT REPORT")
    print("=" * 60)
    print(f"  Dictionary entries:  {stats['total_entries']}")
    print(f"  Source strings:      {stats['source_strings']}")
    print()

    if results["untranslated"]:
        print(f"❌ UNTRANSLATED ({stats['untranslated_count']})")
        print(f"   Strings found in source but missing from dictionary:")
        for s in results["untranslated"][:15]:
            print(f"   - {s[:80]}")
        if len(results["untranslated"]) > 15:
            print(f"   ... and {len(results['untranslated']) - 15} more")
        print()

    if results["orphaned"]:
        print(f"👻 ORPHANED ({stats['orphaned_count']})")
        print(f"   Translations with no matching source string:")
        for s in results["orphaned"][:10]:
            print(f"   - {s[:80]}")
        if len(results["orphaned"]) > 10:
            print(f"   ... and {len(results['orphaned']) - 10} more")
        print()

    if results["identical"]:
        print(f"🔁 IDENTICAL KEY=VALUE ({stats['identical_count']})")
        print(f"   Possibly untranslated (same text in both languages):")
        for s in results["identical"][:10]:
            print(f"   - {s[:80]}")
        if len(results["identical"]) > 10:
            print(f"   ... and {len(results['identical']) - 10} more")
        print()

    if results["empty"]:
        print(f"📭 EMPTY TRANSLATIONS ({stats['empty_count']})")
        for s in results["empty"][:10]:
            print(f"   - {s[:80]}")
        print()

    if results["junk"]:
        print(f"🗑️  JUNK/DEBUG ({stats['junk_count']})")
        print(f"   Debug messages, code, docstrings that shouldn't be translated:")
        for s in results["junk"][:10]:
            print(f"   - {s[:80]}")
        if len(results["junk"]) > 10:
            print(f"   ... and {len(results['junk']) - 10} more")
        print()

    # Summary
    health = stats['total_entries'] - stats['junk_count'] - stats['empty_count']
    coverage = 0
    if stats['source_strings']:
        matched = stats['source_strings'] - stats['untranslated_count']
        coverage = (matched / stats['source_strings']) * 100

    print("=" * 60)
    print(f"  Translation coverage: {coverage:.1f}%")
    print(f"  Healthy entries:      {health}")
    print(f"  Issues found:         {stats['untranslated_count'] + stats['junk_count'] + stats['empty_count']}")
    print("=" * 60)
