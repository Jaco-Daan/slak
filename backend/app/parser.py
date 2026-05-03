"""
Paradox Interactive .txt AST parser.

Implements the tokenization + recursive parsing described in spec ch. 5.
Produces Python dicts where:
  - duplicate keys at the same scope collapse into a Python list
  - nested `name = { ... }` blocks become nested dicts
"""

import re
from typing import Any

TITLE_PREFIXES = ("h_", "e_", "k_", "d_", "c_", "b_")


def tokenize(text: str) -> list[str]:
    """Strip comments, pad structural chars, split preserving quoted strings."""
    # 1. Remove comments (# ... end of line)
    text = re.sub(r"#[^\n]*", "", text)

    # 2. Pad braces and equals signs with spaces so they isolate as tokens
    text = re.sub(r"([{}=])", r" \1 ", text)

    # 3. Split, preserving double-quoted substrings as single tokens
    tokens: list[str] = []
    pattern = re.compile(r'"[^"]*"|\S+')
    for match in pattern.finditer(text):
        tok = match.group(0)
        # Strip surrounding quotes (but keep the literal content)
        if tok.startswith('"') and tok.endswith('"'):
            tok = tok[1:-1]
        tokens.append(tok)
    return tokens


class _Cursor:
    __slots__ = ("tokens", "i")

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def eof(self) -> bool:
        return self.i >= len(self.tokens)


def _assign(scope: dict, key: str, value: Any) -> None:
    """Assign respecting the duplicate-key edge case (collapse into list)."""
    if key in scope:
        existing = scope[key]
        if isinstance(existing, list):
            existing.append(value)
        else:
            scope[key] = [existing, value]
    else:
        scope[key] = value


def _parse_block(cur: _Cursor, until_brace: bool) -> dict | list:
    """
    Parse tokens until either EOF (if not until_brace) or a closing '}'.

    A block is normally a dict of key=value entries. If we encounter a bare
    value (no '=' after it), the block is treated as a list literal — this
    matches the Paradox `colors = { 1 2 3 }` style.
    """
    scope: dict = {}
    list_items: list = []
    is_list = False

    while not cur.eof():
        tok = cur.peek()
        if tok == "}":
            cur.take()
            return list_items if is_list else scope
        if tok == "{":
            # Anonymous nested block as a list item
            cur.take()
            inner = _parse_block(cur, until_brace=True)
            list_items.append(inner)
            is_list = True
            continue

        cur.take()  # consume the key/value token

        # Look ahead: is this `key = ...` or a bare list element?
        if cur.peek() == "=":
            cur.take()  # consume '='
            nxt = cur.peek()
            if nxt is None:
                break
            if nxt == "{":
                cur.take()
                value = _parse_block(cur, until_brace=True)
            else:
                value = cur.take()
            _assign(scope, tok, value)
        else:
            # Bare token = list element
            list_items.append(tok)
            is_list = True

        if not until_brace and cur.eof():
            break

    return list_items if is_list else scope


def parse(text: str) -> dict:
    """Parse a Paradox .txt document into a dict (or list) AST."""
    tokens = tokenize(text)
    cur = _Cursor(tokens)
    result = _parse_block(cur, until_brace=False)
    if isinstance(result, list):
        # Top-level was a list; wrap so callers always get a dict shape
        return {"_root": result}
    return result


# ---------------------------------------------------------------------------
# Title hierarchy transformation (spec 5.3)
# ---------------------------------------------------------------------------

def _is_title_key(key: str) -> bool:
    return any(key.startswith(p) for p in TITLE_PREFIXES)


def _tier_of(key: str) -> str:
    return {
        "h_": "hegemony",
        "e_": "empire",
        "k_": "kingdom",
        "d_": "duchy",
        "c_": "county",
        "b_": "barony",
    }[key[:2]]


def transform_titles(ast: dict) -> dict:
    """
    Walk a parsed landed_titles AST and produce a recursive Title tree.

    Each Title has: id, tier, is_landed, metadata, children (dict of id -> Title)
    `metadata` collects all non-title keys (color, capital, cultural_names...).
    """
    def walk(node: dict, key: str | None) -> dict:
        children: dict[str, dict] = {}
        metadata: dict = {}
        for k, v in node.items():
            if isinstance(k, str) and _is_title_key(k) and isinstance(v, dict):
                children[k] = walk(v, k)
            else:
                metadata[k] = v

        is_landed = True
        if key is not None and key.startswith("h_"):
            # Hegemony edge case — landed iff at least one child is a map title
            is_landed = any(_is_title_key(ck) for ck in children.keys())

        return {
            "id": key,
            "tier": _tier_of(key) if key else "root",
            "is_landed": is_landed,
            "metadata": metadata,
            "children": children,
        }

    root = walk(ast, None)
    # Return only the named top-level titles, not the synthetic root
    return root["children"]


# ---------------------------------------------------------------------------
# Trait + Death extraction (spec 5.4)
# ---------------------------------------------------------------------------

def extract_genetic_traits(ast: dict) -> list[dict]:
    """Return list of {id, group, level, birth_chance, random_creation, opposites}."""
    traits: list[dict] = []
    for trait_id, body in ast.items():
        if not isinstance(body, dict):
            continue
        if body.get("genetic") != "yes":
            continue
        opposites_raw = body.get("opposites", [])
        if isinstance(opposites_raw, str):
            opposites = [opposites_raw]
        elif isinstance(opposites_raw, list):
            opposites = [o for o in opposites_raw if isinstance(o, str)]
        else:
            opposites = []

        def _f(key: str, default: float) -> float:
            v = body.get(key, default)
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        def _i(key: str, default: int) -> int:
            v = body.get(key, default)
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        traits.append({
            "id": trait_id,
            "group": body.get("group", trait_id),
            "level": _i("level", 1),
            "birth_chance": _f("birth_chance", 0.0),
            "random_creation": _f("random_creation", 0.0),
            "opposites": opposites,
        })
    return traits


def extract_death_reasons(ast: dict) -> list[dict]:
    """Return list of {id, is_natural, required_trait}."""
    reasons: list[dict] = []
    for death_id, body in ast.items():
        if not isinstance(body, dict):
            continue
        is_natural = body.get("natural") == "yes"
        required_trait = None
        trigger = body.get("natural_death_trigger")
        if isinstance(trigger, dict):
            ht = trigger.get("has_trait")
            if isinstance(ht, str):
                required_trait = ht
        reasons.append({
            "id": death_id,
            "is_natural": is_natural,
            "required_trait": required_trait,
        })
    return reasons
