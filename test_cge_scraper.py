import importlib.util
import os
import sys
from types import SimpleNamespace

import pytest


def load_main_module():
    """Load main.py as a fresh module so tests can modify its globals safely."""
    root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(root, "main.py")
    spec = importlib.util.spec_from_file_location("test_main_module", script_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_sanitize_basic():
    mod = load_main_module()
    out = mod.sanitize_param("Registro de Matrícula Consular-Altas")
    # accept either with or without the combined accent handling depending on environment
    assert out.startswith("registro")


def test_sanitize_accents():
    mod = load_main_module()
    assert mod.sanitize_param("áéíóú ñ - prueba") == "aeiounprueba"


def test_send_message_posts(monkeypatch):
    mod = load_main_module()

    # Provide a fake config via get_config
    cfg = {"api": {"base_url": "http://api.test", "key": "K"}, "chat": {"chat_id": "C"}}
    monkeypatch.setattr(mod, "get_config", lambda path=None: cfg)

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})

    monkeypatch.setattr(mod.requests, "post", fake_post)

    # Call send_message and assert three posts (start, sendText, stop)
    mod.send_message("hola mundo")

    assert len(calls) == 3
    assert calls[0]["url"].endswith("/sessions/default/start")
    assert calls[1]["url"].endswith("/sendText")
    assert calls[1]["json"]["text"] == "hola mundo"
    assert calls[2]["url"].endswith("/sessions/default/stop")


def test_main_creates_file_and_sends_message(monkeypatch, tmp_path):
    mod = load_main_module()

    search_text = "MiFila"
    fecha = "2025-10-21"
    # HTML contains a single row with four columns (last has a link)
    html = f"""
    <html><body>
    <table>
      <tr>
        <td>{search_text}</td>
        <td>{fecha}</td>
        <td>ignored</td>
        <td><a href="/detalle">ver</a></td>
      </tr>
    </table>
    </body></html>
    """

    # stub get_config to return a web url base
    cfg = {"web": {"url": "http://example.com"}}
    monkeypatch.setattr(mod, "get_config", lambda path=None: cfg)

    # stub requests.get
    class FakeResp:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=30: FakeResp(html.encode("utf-8")))

    sent = []
    monkeypatch.setattr(mod, "send_message", lambda m: sent.append(m))

    # ensure module's __file__ points to tmp_path so fecha_ file is created there
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "main.py"))

    # run main
    params = SimpleNamespace(text=search_text, config=None)
    mod.main(params)

    fname = tmp_path / f"fecha_{mod.sanitize_param(search_text)}.txt"
    assert fname.exists()
    assert fname.read_text(encoding="utf-8") == fecha
    assert len(sent) == 1
    assert fecha in sent[0]


def test_main_no_change_does_not_send(monkeypatch, tmp_path):
    mod = load_main_module()

    search_text = "MiFila"
    fecha = "2025-10-21"
    html = f"""
    <html><body>
    <table>
      <tr>
        <td>{search_text}</td>
        <td>{fecha}</td>
        <td>ignored</td>
        <td><a href="/detalle">ver</a></td>
      </tr>
    </table>
    </body></html>
    """

    cfg = {"web": {"url": "http://example.com"}}
    monkeypatch.setattr(mod, "get_config", lambda path=None: cfg)
    class FakeResp:
        def __init__(self, content):
            self.content = content
        def raise_for_status(self):
            return None
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=30: FakeResp(html.encode("utf-8")))

    sent = []
    monkeypatch.setattr(mod, "send_message", lambda m: sent.append(m))
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "main.py"))

    # create the fecha file with the same fecha to simulate no-change
    fname = tmp_path / f"fecha_{mod.sanitize_param(search_text)}.txt"
    fname.write_text(fecha, encoding="utf-8")

    params = SimpleNamespace(text=search_text, config=None)
    mod.main(params)

    # file remains and no message sent
    assert fname.exists()
    assert fname.read_text(encoding="utf-8") == fecha
    assert sent == []


def test_main_row_not_found_exits(monkeypatch):
    mod = load_main_module()
    html = "<html><body><table><tr><td>Other</td><td>2020</td></tr></table></body></html>"
    cfg = {"web": {"url": "http://example.com"}}
    monkeypatch.setattr(mod, "get_config", lambda path=None: cfg)
    class FakeResp:
        def __init__(self, content):
            self.content = content
        def raise_for_status(self):
            return None
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=30: FakeResp(html.encode("utf-8")))

    with pytest.raises(SystemExit) as exc:
        mod.main(SimpleNamespace(text="MiFila", config=None))
    assert exc.value.code == 2


def test_main_row_missing_columns_exits(monkeypatch, tmp_path):
    mod = load_main_module()
    # row with only one column
    html = "<html><body><table><tr><td>MiFila</td></tr></table></body></html>"
    cfg = {"web": {"url": "http://example.com"}}
    monkeypatch.setattr(mod, "get_config", lambda path=None: cfg)
    class FakeResp:
        def __init__(self, content):
            self.content = content
        def raise_for_status(self):
            return None
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=30: FakeResp(html.encode("utf-8")))
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "main.py"))

    with pytest.raises(SystemExit) as exc:
        mod.main(SimpleNamespace(text="MiFila", config=None))
    assert exc.value.code == 4


def test_get_config_creates_template_and_exits(monkeypatch, tmp_path):
    mod = load_main_module()
    # point module __file__ to tmp_path so config.toml location is under tmp_path
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "main.py"))
    cfg_path = tmp_path / "config.toml"
    # ensure it does not exist
    if cfg_path.exists():
        cfg_path.unlink()

    with pytest.raises(SystemExit) as exc:
        mod.get_config()

    # created example config and exited with code 1
    assert cfg_path.exists()
    assert exc.value.code == 1
