"""Tests für categories/detectors/storage.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.storage import detect_ssd_gb, detect_hdd_gb, detect_nvme


# ---------- detect_ssd_gb ----------

def test_ssd_gb_direkt():
    assert detect_ssd_gb("Office PC 256GB SSD i5-8500") == 256


def test_ssd_vor_zahl():
    assert detect_ssd_gb("Office PC SSD 256GB i5-8500") == 256


def test_ssd_tb_umrechnung():
    assert detect_ssd_gb("Gaming PC 1TB SSD RTX 3060") == 1000


def test_ssd_tb_dezimalkomma():
    assert detect_ssd_gb("Gaming PC 1,5TB SSD RTX 3070") == 1500


def test_ssd_tb_dezimalpunkt():
    assert detect_ssd_gb("Gaming PC 1.5TB SSD RTX 3070") == 1500


def test_ssd_nvme_zaehlt_als_ssd():
    assert detect_ssd_gb("Gaming PC 512GB NVMe RTX 3060") == 512


def test_ssd_nvme_ssd_kombiniert():
    assert detect_ssd_gb("Gaming PC 512GB NVMe SSD RTX 3060") == 512


def test_ssd_nicht_mit_ram_verwechseln():
    # kritischer Kollisionsfall wie beim RAM-Detector, nur umgekehrt
    assert detect_ssd_gb("Gaming PC 16GB RAM 512GB SSD Ryzen 5") == 512


def test_ssd_kein_treffer_reine_gpu():
    assert detect_ssd_gb("ASUS RTX 3060 12GB TUF Gaming") is None


def test_ssd_kein_treffer_ohne_ssd_erwaehnung():
    assert detect_ssd_gb("Gaming PC 16GB RAM 1TB HDD Ryzen 5") is None


def test_ssd_bekannte_grenze_ohne_einheit():
    # "500ssd" ohne "GB"/"TB" -- bewusst kein Treffer (siehe Docstring)
    assert detect_ssd_gb("i7-14700k 32gb ddr5 500ssd rtx3060ti") is None


def test_ssd_bekannte_grenze_bindestrich_dezimalzahl():
    # Bindestrich als Dezimaltrenner ("1-5TB" statt "1,5TB"/"1.5TB") wird
    # NICHT unterstuetzt -- kommt in echten Anzeigentiteln nicht vor
    # (nur als URL-Slug-Artefakt). Dokumentiert die bekannte Fehlinter-
    # pretation: der Bindestrich trennt die Zahlen, "5TB" wird isoliert
    # erkannt statt "1,5TB" als Ganzes.
    assert detect_ssd_gb("Gaming PC 1-5TB SSD RTX 3060") == 5000


def test_ssd_tippfehler_sdd_vor_zahl():
    # "SDD" ist ein haeufiger Vertipper fuer "SSD" in echten Kleinanzeigen-
    # Titeln (Schritt A) und soll gleichwertig erkannt werden.
    assert detect_ssd_gb("Office PC SDD 256GB i5-8500") == 256


def test_ssd_tippfehler_sdd_nach_zahl():
    assert detect_ssd_gb("Gaming PC 512GB SDD RTX 3060") == 512


def test_ssd_tippfehler_sdd_case_insensitive():
    assert detect_ssd_gb("PC mit 500gb sdd speicher") == 500


# ---------- SATA-Generationsangabe zwischen Groesse und "SSD" (STATUS.md
# Abschnitt 10, vormals offener Befund -- jetzt behoben) ----------

def test_ssd_bloss_sata_zwischen_zahl_und_ssd():
    # Bereits vor diesem Fix funktionierender Fall (Regressionsschutz).
    assert detect_ssd_gb("Kingston A400 250GB SATA SSD 2.5") == 250


def test_ssd_sata_iii_zwischen_zahl_und_ssd():
    assert detect_ssd_gb("500GB SATA III SSD") == 500


def test_ssd_sata_mit_bindestrich_generation():
    assert detect_ssd_gb("500GB SATA-III SSD") == 500


def test_ssd_sata_generation_als_ziffer_mit_leerzeichen():
    assert detect_ssd_gb("500GB SATA 3 SSD") == 500


def test_ssd_sata_generation_als_ziffer_ohne_leerzeichen():
    assert detect_ssd_gb("500GB SATA3 SSD") == 500


def test_ssd_sata_iii_case_insensitive():
    assert detect_ssd_gb("500gb sata iii ssd") == 500


def test_ssd_sata_iii_umgekehrte_wortstellung():
    # SSD-Schluesselwort vor der Groessenangabe, SATA III dazwischen.
    assert detect_ssd_gb("SSD SATA III 500GB") == 500


# ---------- detect_hdd_gb ----------

def test_hdd_gb_direkt():
    assert detect_hdd_gb("PC 1TB HDD zusätzlich zur SSD") == 1000


def test_hdd_vor_zahl():
    assert detect_hdd_gb("PC HDD: 2TB zusätzlich") == 2000


def test_hdd_und_ssd_im_gleichen_titel_nicht_verwechseln():
    assert detect_hdd_gb("Gaming PC 512GB SSD + 2TB HDD RTX 3060") == 2000
    assert detect_ssd_gb("Gaming PC 512GB SSD + 2TB HDD RTX 3060") == 512


def test_hdd_kein_treffer_nur_ssd():
    assert detect_hdd_gb("Office PC 256GB SSD i5-8500") is None


# ---------- detect_nvme ----------

def test_nvme_erkannt():
    assert detect_nvme("Gaming PC 512GB NVMe SSD RTX 3060") is True


def test_nvme_nicht_erkannt_bei_reiner_sata_ssd():
    assert detect_nvme("Office PC 256GB SSD i5-8500") is False


def test_nvme_case_insensitive():
    assert detect_nvme("PC mit 512gb nvme speicher") is True


def test_nvme_kein_treffer_leerer_text():
    assert detect_nvme("") is False


def test_ssd_realer_titel_mit_komma_dezimal():
    r = detect_ssd_gb("Gaming PC i5-12600K RX 6700 XT 12GB 32GB RAM 1,5TB SSD")
    assert r == 1500


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
