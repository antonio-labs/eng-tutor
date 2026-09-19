from pathlib import Path

from app.main import create_app


STATIC_DIR = Path(__file__).parents[1] / "app" / "static"


def test_app_serves_three_view_frontend(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db")
    paths = {route.path for route in app.routes}
    html = (STATIC_DIR / "index.html").read_text()
    javascript = (STATIC_DIR / "app.js").read_text()

    assert {"/", "/static", "/api/health"} <= paths
    assert "#app" in javascript
    assert "renderHome" in javascript
    assert "renderLesson" in javascript
    assert "renderResult" in javascript
    assert "innerHTML" not in javascript
    assert "—" not in html + javascript
