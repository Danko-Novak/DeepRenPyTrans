"""
Smart string filters for Ren'Py script extraction.
Determines which strings are translatable human-readable text vs internal IDs/code.
"""

import re


class TranslatableFilter:
    """
    Configurable filter that decides if a string extracted from .rpy files
    is translatable (human-readable text) or should be skipped (code, IDs, paths).
    """

    def __init__(
        self,
        skip_prefixes: list = None,
        force_include: list = None,
        force_exclude: list = None,
        min_length: int = 2,
    ):
        self.skip_prefixes = tuple(skip_prefixes or [])
        self.force_include = set(force_include or [])
        self.force_exclude = set(force_exclude or [])
        self.min_length = min_length

        # Pre-compiled patterns
        self._hex_color = re.compile(r'^#[0-9a-fA-F]{3,8}$')
        self._pure_tag = re.compile(r'^\{[^}]+\}$')
        self._pure_var = re.compile(r'^\[[^\]]+\]$')
        self._all_caps_id = re.compile(r'^[A-Z0-9_]+$')
        self._snake_case = re.compile(r'^[a-z0-9_]+$')
        self._mixed_underscore = re.compile(r'^[A-Za-z0-9_]+$')
        self._camel_case = re.compile(r'[a-z][A-Z]')
        self._alpha_numeric = re.compile(r'^[A-Za-z0-9]+$')
        self._math_only = re.compile(r'^[-+0-9.,*:/ \(\)\{\}\[\]\\_]+$')
        self._cyrillic = re.compile(r'[а-яА-ЯёЁ]')
        self._debug_pattern = re.compile(
            r'(?:self\.|actor\.|{self\.|{actor\.|\.\w+\(|'
            r'initialized|mode|singleton|migration|scrubber|'
            r'housekeeping aborted|debug tracking|'
            r'__\w+__|assert|docstring)',
            re.IGNORECASE
        )

        # Common short words to preserve (not IDs)
        self._preserve_short = {"OK", "NO", "UI", "ON", "XP", "HP", "MP"}
        # Known non-translatable lowercase words
        self._skip_lowercase = {
            "urm", "eaiou", "sfx1", "sfx2", "sfx3", "sfx4",
            "game", "sfx", "that", "this", "with", "true", "false", "none",
        }

    def is_translatable(self, s: str) -> bool:
        """
        Returns True if the string should be translated, False if it should be skipped.
        """
        s_strip = s.strip()

        # Force include/exclude overrides
        if s_strip in self.force_include:
            return True
        if s_strip in self.force_exclude:
            return False

        # Length check
        if len(s_strip) < self.min_length:
            if s_strip not in ["?", "!", ".", "..."]:
                return False

        # --- Structural filters ---

        # Contains dots/brackets/parens but NO spaces → likely Python expression
        if any(c in s_strip for c in ".[()]") and " " not in s_strip:
            return False

        # Logic expressions
        logic_ops = ["==", "!=", ">=", "<=", ".isAt(", "GAME.", "REGISTRY.",
                      ".attr[", ".done", " in ", " and ", " or ", " not "]
        if any(op in s_strip for op in logic_ops):
            return False

        # File paths
        if "/" in s_strip or "\\" in s_strip:
            return False
        path_exts = (".png", ".ogg", ".jpg", ".mp3", ".rpy", ".rpyc",
                     ".py", ".rpym", ".ttf", ".webp", ".wav")
        if s_strip.endswith(path_exts):
            return False

        # Hex colors
        if self._hex_color.match(s_strip):
            return False

        # Pure tags or variables
        if self._pure_tag.match(s_strip) or self._pure_var.match(s_strip):
            return False

        # --- Single-word analysis ---
        if " " not in s_strip:
            s_upper = s_strip.upper()

            # All-caps IDs (e.g., MINING_YIELD)
            if self._all_caps_id.match(s_strip) and len(s_strip) > 5:
                return False

            # snake_case IDs
            if self._snake_case.match(s_strip) and "_" in s_strip:
                return False

            # Mixed_Case_Underscored
            if "_" in s_strip and self._mixed_underscore.match(s_strip):
                return False

            # camelCase
            if self._camel_case.search(s_strip) and self._alpha_numeric.match(s_strip):
                return False

            # Configurable prefix IDs
            if self.skip_prefixes and s_upper.startswith(self.skip_prefixes):
                return False

            # 2-letter uppercase codes
            if len(s_strip) == 2 and s_strip.isupper() and s_strip not in self._preserve_short:
                return False

            # Single lowercase word → internal ID or Ren'Py keyword
            if s_strip.islower():
                return False

        # Already contains Cyrillic/target-language text
        if self._cyrillic.search(s_strip):
            return False

        # Math-only / pure placeholder strings
        if self._math_only.match(s_strip) and not any(c.isalpha() for c in s_strip):
            return False

        # Internal variable templates
        if s_strip.endswith(("_{}", "_smart", "_found", "_done")):
            return False
        if s_strip.lower() in self._skip_lowercase:
            return False

        # Debug/error patterns (docstrings, assertions, debug logs)
        if self._debug_pattern.search(s_strip):
            return False

        # Variable references in f-string style
        if s_strip.count("{") > 2 and ", {" in s_strip:
            return False

        return True

    def is_junk(self, key: str, value: str) -> bool:
        """
        Check if a dictionary entry is "junk" — debug strings, code artifacts, etc.
        Returns True if the entry should be removed from the translation dictionary.
        """
        k = key.strip()

        # Debug/assertion messages
        if self._debug_pattern.search(k):
            return True

        # Code conditions (e.g., "khelara.wears('ITMUniformKrell')")
        if ".wears(" in k or ".getTally(" in k or ".isShaved()" in k:
            return True

        # Python docstrings
        docstring_markers = [
            "Getter with lazy initialization",
            "Return list of reachable",
            "Helper to compile visible",
            "Callback called continuously",
            "Always initialize loadout",
            "Returns where an item is",
        ]
        if any(marker in k for marker in docstring_markers):
            return True

        # Logging format strings
        if k.strip() == "[%(levelname)s] %(name)s: %(message)s":
            return True

        return False
