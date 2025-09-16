#!/usr/bin/env python3
"""Test script to run the LogicEngine API server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from logicengine.api import app
    import uvicorn
    
    print("✅ API imported successfully")
    print("🚀 Starting server on http://127.0.0.1:8000")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        access_log=True
    )
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
