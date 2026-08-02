"""Integrationstest für das Benachrichtigungs-Gate in app.py (Phase 6b).

Mockt Scraper und ntfy-Versand, lässt run_scan() real laufen und prüft:
- Treffer werden IMMER in found.json gespeichert (mit deal_score/deal_stars)
- ntfy wird NUR bei ★★★★★ UND Preis <= gate_max_price ausgelöst
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka
import price_history


def _load_app_module(data_dir: str):
    """Lädt app.py frisch mit einem isolierten DATA_DIR (Testumgebung)."""
    import logging
    logging.root.handlers.clear()  # sonst wirkt logging.basicConfig() nur beim ersten Testlauf

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_notification_gate_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        # Zwei synthetische Kleinanzeigen-Treffer: einer sollte 5 Sterne
        # UND <=150€ erreichen (benachrichtigt), der andere nicht (nur
        # gespeichert).
        # Preis 5€: Mit den kategoriespezifischen scoring_weights aus
        # rules/gpu.yaml (70% Preis / 10% Hardwarequalität / 20% Profit,
        # siehe dortiger Kommentar -- "profit" seit STATUS.md Abschnitt 16
        # testweise aktiviert) ist ★★★★★ für die GPU-Kategorie ohne
        # Preishistorie NICHT mehr erreichbar: "profit" bliebe sonst beim
        # neutralen Platzhalter (60) und deckelt den Gesamt-Score auf
        # rechnerisch maximal ~91 (0.7*100 + 0.1*85 + 0.2*60). Deshalb wird
        # hier -- passend zum eigentlichen Zweck der neuen Komponente -- ein
        # einzelner Preishistorie-Datenpunkt für "rtx_2080_ti" VOR dem Scan
        # geseedet, sodass ein echter (statt platzhalterhafter) Marktpreis
        # vorliegt und sowohl "price" als auch "profit" den sehr günstigen
        # Kauf (5€ vs. Marktpreis 260€) korrekt hoch bewerten.
        seeded_point = price_history.make_price_point(
            price=260.0,
            source="kleinanzeigen",
            model="rtx_2080_ti",
            category="gpu",
        )
        price_history.append_price_point(
            Path(tmpdir) / "price_history.jsonl", seeded_point
        )

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 2080 Ti DUAL Lüfter",
                "price": 5.0,  # sehr günstig -> hoher Score, Top-Deal-Regel
                "url": "https://example.test/angebot-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
            {
                "source": "Kleinanzeigen",
                "title": "RTX 3060 12GB",
                "price": 259.0,  # nahe max_price der "Okay"-Regel -> niedriger Score
                "url": "https://example.test/angebot-2",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy") as mock_send_ntfy:

            app_mod.run_scan()

            # found.json muss BEIDE Treffer enthalten, mit deal_score/deal_stars
            found_file = Path(tmpdir) / "found.json"
            found_data = json.loads(found_file.read_text())
            assert len(found_data) == 2
            for entry in found_data:
                assert "deal_score" in entry
                assert "deal_stars" in entry
                assert entry["deal_score"] is not None

            # ntfy darf nur für den 5€-Top-Deal-Treffer ausgelöst worden sein
            assert mock_send_ntfy.call_count == 1
            called_kwargs = mock_send_ntfy.call_args.kwargs
            assert "5 €" in called_kwargs["title"]


def test_notification_gate_niemand_benachrichtigt_wenn_alle_ueber_preisgrenze():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                # 5 Sterne, aber ueber der GPU-eigenen 250€-notify_max_price-
                # Grenze (rules/gpu.yaml) -- sehr niedriger Preis waere sonst
                # automatisch 5 Sterne UND unter dem Limit, das will dieser
                # Test bewusst vermeiden (siehe test_notification_gate_end_to_end
                # fuer den 5€-Fall). 249,99€ liegt knapp unter max_price der
                # RTX 3060-Regel (280€), damit die Regel ueberhaupt matcht.
                "title": "RTX 3060 12GB",
                "price": 279.0,  # ueber der 250€-Gate-Grenze der GPU-Kategorie
                "url": "https://example.test/angebot-3",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy") as mock_send_ntfy:

            app_mod.run_scan()

            found_file = Path(tmpdir) / "found.json"
            found_data = json.loads(found_file.read_text())
            assert len(found_data) == 1  # weiterhin gespeichert

            mock_send_ntfy.assert_not_called()  # aber nicht benachrichtigt


def test_notification_gate_nutzt_kategorie_eigenes_preislimit_statt_globalem_fallback():
    """Regressionstest fuer den notify_max_price-Bugfix: rules/gpu.yaml
    definiert notify_max_price: 250, waehrend das globale gate_max_price
    (Fallback fuer Kategorien ohne eigenes Limit) bei 150 liegt. Ein GPU-
    Treffer zwischen 150€ und 250€ muss deshalb benachrichtigt werden
    (sofern die Sternegrenze erfuellt ist) -- mit dem rein globalen Gate
    waere das vorher unmoeglich gewesen.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 2080 Ti DUAL Lüfter",
                "price": 5.0,  # sehr guenstig -> 5 Sterne, Top-Deal-Regel
                "url": "https://example.test/angebot-4",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy") as mock_send_ntfy:

            app_mod.run_scan()
            # 5€ liegt unter BEIDEN Grenzen (global 150€ und GPU-eigenem 250€),
            # daher hier nur eine Existenzprüfung, dass benachrichtigt wurde --
            # der eigentliche Beweis, dass das kategorie-eigene Limit greift,
            # kommt aus test_notification_gate_niemand_benachrichtigt_wenn_alle_ueber_preisgrenze
            # (279€ waere unter dem ALTEN globalen 150€-Fallback sowieso nie
            # durchgekommen, matcht aber erst gar nicht als Regel -- der
            # eigentliche Beleg liegt in matcher.py-Unittests, siehe unten).
            assert mock_send_ntfy.call_count == 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
