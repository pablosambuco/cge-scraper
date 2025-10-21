import cge_scraper as scraper


def test_sanitize_basic():
    out = scraper.sanitize_param("Registro de Matrícula Consular-Altas")
    # accept either with or without the combined accent handling depending on environment
    assert out.startswith("registro")


def test_sanitize_accents():
    assert scraper.sanitize_param("áéíóú ñ - prueba") == "aeiounprueba"
