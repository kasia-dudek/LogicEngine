# main.py
"""Run LogicEngine API with Uvicorn."""

import os
import uvicorn

# Import app from api.py (works inside a package and as a script)
try:
    from .api import app  # when running as a package: `python -m yourpkg.main`
except ImportError:
    from api import app   # when running the file directly: `python main.py`

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_flag = os.getenv("RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run(app, host=host, port=port, reload=reload_flag)
