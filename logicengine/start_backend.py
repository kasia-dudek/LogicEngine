#!/usr/bin/env python3
"""Simple script to start the FastAPI backend."""

import uvicorn
from src.logicengine.api import app

if __name__ == "__main__":
    print("Starting LogicEngine backend on http://127.0.0.1:8000")
    uvicorn.run("src.logicengine.api:app", host="127.0.0.1", port=8000, reload=True)


