#!/usr/bin/env python3
"""
DeepRenPyTrans — AI-powered universal Ren'Py game translator.

Usage:
    python -m deeprenpytrans extract  --game ./MyGame/game
    python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
    python -m deeprenpytrans audit    --dict dictionary.json [--strings strings.json]
    python -m deeprenpytrans clean    --dict dictionary.json [--strings strings.json]
    python -m deeprenpytrans inject   --game ./MyGame/game --lang russian
"""

import argparse
import os
import sys

from . import __version__
from .config import load_config
from .extractor import extract_strings
from .translator import translate
from .auditor import audit, clean_dictionary
from .hooks_generator import generate_hooks


def cmd_extract(args, config):
    """Extract translatable strings from .rpy files."""
    game_dir = args.game or config.get("game_dir", ".")
    output = args.output or "strings_by_file.json"
    log_path = args.include_log

    if not os.path.isdir(game_dir):
        print(f"❌ Game directory not found: {game_dir}")
        sys.exit(1)

    print(f"🔍 Extracting strings from: {game_dir}")
    extract_strings(
        game_dir=game_dir,
        output_path=output,
        filter_config=config.get("extraction", {}),
        include_log=log_path,
        verbose=True,
    )


def cmd_translate(args, config):
    """Translate extracted strings using AI."""
    strings_path = args.strings or "strings_by_file.json"
    dict_path = args.dict

    if not dict_path:
        game_dir = config.get("game_dir", ".")
        tl_dir = config.get("translation_dir", "russian")
        dict_path = os.path.join(game_dir, "tl", tl_dir, "dictionary.json")

    if not os.path.exists(strings_path):
        print(f"❌ Strings file not found: {strings_path}")
        print("   Run 'extract' first to generate it.")
        sys.exit(1)

    api_key = config["api"].get("api_key", "")
    if not api_key and config["api"]["provider"] != "ollama":
        print("❌ No API key found!")
        print("   Set it in .env file or as environment variable.")
        print(f"   Expected: {config['api'].get('provider', 'DEEPSEEK').upper()}_API_KEY")
        sys.exit(1)

    print(f"🤖 Translating to {config['target_language']}...")
    print(f"   Provider: {config['api']['provider']} ({config['api']['model']})")
    print(f"   Dictionary: {dict_path}\n")

    translate(
        strings_path=strings_path,
        dict_path=dict_path,
        config=config,
        verbose=True,
    )


def cmd_audit(args, config):
    """Audit translation dictionary for issues."""
    dict_path = args.dict
    strings_path = args.strings

    if not os.path.exists(dict_path):
        print(f"❌ Dictionary not found: {dict_path}")
        sys.exit(1)

    audit(
        dict_path=dict_path,
        strings_path=strings_path,
        filter_config=config.get("extraction", {}),
        verbose=True,
    )


def cmd_clean(args, config):
    """Clean dictionary of junk/orphaned entries."""
    dict_path = args.dict
    strings_path = args.strings

    if not os.path.exists(dict_path):
        print(f"❌ Dictionary not found: {dict_path}")
        sys.exit(1)

    clean_dictionary(
        dict_path=dict_path,
        strings_path=strings_path,
        filter_config=config.get("extraction", {}),
        remove_junk=not args.keep_junk,
        remove_orphaned=args.remove_orphaned,
        dry_run=args.dry_run,
        verbose=True,
    )


def cmd_inject(args, config):
    """Generate hooks.rpy for runtime translation injection."""
    game_dir = args.game or config.get("game_dir", ".")
    lang_dir = args.lang or config.get("translation_dir", "russian")
    output_dir = os.path.join(game_dir, "tl", lang_dir)

    fonts_config = config.get("fonts", {})
    hooks_config = config.get("hooks", {})

    generate_hooks(
        output_dir=output_dir,
        lang_dir=lang_dir,
        hotkey=hooks_config.get("toggle_hotkey", "l"),
        default_font=fonts_config.get("default", "DejaVuSans.ttf"),
        font_replacements=fonts_config.get("replacements"),
        verbose=True,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="deeprenpytrans",
        description="🎮 DeepRenPyTrans — AI-powered Ren'Py game translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s extract  --game ./MyGame/game
  %(prog)s translate --strings strings.json --dict ./MyGame/game/tl/russian/dictionary.json
  %(prog)s audit    --dict dictionary.json --strings strings.json
  %(prog)s clean    --dict dictionary.json --dry-run
  %(prog)s inject   --game ./MyGame/game --lang russian
        """,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config.yaml")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- extract ---
    p_extract = subparsers.add_parser("extract", help="Extract translatable strings from .rpy files")
    p_extract.add_argument("--game", help="Path to game/ directory")
    p_extract.add_argument("--output", "-o", default="strings_by_file.json", help="Output JSON file")
    p_extract.add_argument("--include-log", help="Path to untranslated.log to merge")

    # --- translate ---
    p_translate = subparsers.add_parser("translate", help="Translate strings using AI")
    p_translate.add_argument("--strings", "-s", default="strings_by_file.json", help="Extracted strings JSON")
    p_translate.add_argument("--dict", "-d", help="Path to dictionary.json")

    # --- audit ---
    p_audit = subparsers.add_parser("audit", help="Audit translation quality")
    p_audit.add_argument("--dict", "-d", required=True, help="Path to dictionary.json")
    p_audit.add_argument("--strings", "-s", help="Path to strings_by_file.json")

    # --- clean ---
    p_clean = subparsers.add_parser("clean", help="Clean dictionary of junk entries")
    p_clean.add_argument("--dict", "-d", required=True, help="Path to dictionary.json")
    p_clean.add_argument("--strings", "-s", help="Path to strings_by_file.json")
    p_clean.add_argument("--dry-run", action="store_true", help="Only show what would be removed")
    p_clean.add_argument("--keep-junk", action="store_true", help="Don't remove debug/code strings")
    p_clean.add_argument("--remove-orphaned", action="store_true", help="Remove strings not in source")

    # --- inject ---
    p_inject = subparsers.add_parser("inject", help="Generate hooks.rpy for runtime injection")
    p_inject.add_argument("--game", help="Path to game/ directory")
    p_inject.add_argument("--lang", help="Translation directory name (e.g., russian)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Load config
    config_path = args.config if os.path.exists(args.config) else None
    config = load_config(config_path)

    # Dispatch
    commands = {
        "extract": cmd_extract,
        "translate": cmd_translate,
        "audit": cmd_audit,
        "clean": cmd_clean,
        "inject": cmd_inject,
    }

    commands[args.command](args, config)


if __name__ == "__main__":
    main()
