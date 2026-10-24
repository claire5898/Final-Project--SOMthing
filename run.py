"""Start SOMthing:  python run.py   then open http://127.0.0.1:8000"""

import os
import threading
import webbrowser

import uvicorn

from somthing import config
from somthing.server import create_app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    source = config.load_env()
    url = f"http://127.0.0.1:{port}"
    print("\n  SOMthing is starting…")
    print(f"  AI key: {'found in the ' + source if source else 'NOT found (browsing works, AI features are off)'}")
    print(f"  Open {url} in your browser. Press Ctrl+C to stop.\n")
    if os.getenv("SOMTHING_NO_BROWSER") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")
