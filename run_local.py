import os
import sys
import threading
import webbrowser

from waitress import serve


HOST = "127.0.0.1"
PORT = 5000


# Режим установленного приложения
if getattr(sys, "frozen", False):
    os.environ["DIARIES_INSTALLED"] = "1"


from app import create_app


def open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


app = create_app()


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()

    print("Diaries запущен.")
    print(f"Адрес: http://{HOST}:{PORT}")
    print("Для остановки нажмите Ctrl+C.")

    serve(app, host=HOST, port=PORT)
