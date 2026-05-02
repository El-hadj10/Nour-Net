import threading
import webbrowser

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import uvicorn


def _open_browser():
    webbrowser.open("http://127.0.0.1:8080")


if __name__ == "__main__":
    timer = threading.Timer(1.5, _open_browser)
    timer.start()
    uvicorn.run("web.app:app", host="127.0.0.1", port=8080, reload=False)
