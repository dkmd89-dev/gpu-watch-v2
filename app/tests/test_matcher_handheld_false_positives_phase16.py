"""Phase-16 regression tests for handheld category precision.

Focus: accessory-only, software-only and repair/part listings must not be
classified as complete handhelds, while legitimate device bundles remain
accepted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import evaluate, load_rules

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = load_rules(RULES_DIR)


def _not_handheld(title: str, price: float = 20.0):
    r = evaluate(title, price, _cfg)
    assert r.matched is False, f"Unexpected handheld match: {title!r} -> {r}"


def _is_handheld(title: str, price: float = 220.0):
    r = evaluate(title, price, _cfg)
    assert r.matched is True, f"Expected handheld match: {title!r} -> {r}"
    assert r.category == "handhelds"


# --- accessory / replacement parts ---

def test_steam_deck_controller_standalone_is_excluded():
    _not_handheld("Steam Deck Controller")


def test_steam_deck_joystick_standalone_is_excluded():
    _not_handheld("Steam Deck Joystick Ersatz")


def test_steam_deck_replacement_part_standalone_is_excluded():
    _not_handheld("Steam Deck Replacement Part")


def test_steam_deck_netzeil_standalone_is_excluded():
    _not_handheld("Steam Deck Netzteil 65W")


def test_rog_ally_ladegeraet_standalone_is_excluded():
    _not_handheld("ROG Ally Ladegerät original")


def test_legion_go_anleitung_standalone_is_excluded():
    _not_handheld("Lenovo Legion Go Anleitung")


# --- software / digital content ---

def test_steam_deck_game_standalone_is_excluded():
    _not_handheld("Steam Deck Game Code")


def test_steam_deck_digital_code_standalone_is_excluded():
    _not_handheld("Steam Deck Digital Code")


def test_steam_deck_account_standalone_is_excluded():
    _not_handheld("Steam Deck Account")


def test_ps_vita_spiele_standalone_is_excluded():
    _not_handheld("PS Vita Spiele Sammlung")


# --- real devices / bundles must survive ---

def test_steam_deck_with_power_supply_still_matches():
    _is_handheld("Steam Deck OLED 512GB mit Netzteil", 230.0)


def test_steam_deck_with_games_still_matches():
    _is_handheld("Steam Deck 256GB inkl. 5 Spiele", 220.0)


def test_steam_deck_with_controller_still_matches():
    _is_handheld("Steam Deck OLED mit Controller", 230.0)


def test_rog_ally_with_charger_still_matches():
    _is_handheld("ROG Ally Z1 Extreme mit Ladegerät", 300.0)


def test_legion_go_with_accessories_still_matches():
    _is_handheld("Lenovo Legion Go 512GB inkl. Controller und Ladekabel", 300.0)


def test_steam_deck_plain_title_still_matches():
    _is_handheld("Steam Deck OLED 512GB", 230.0)
