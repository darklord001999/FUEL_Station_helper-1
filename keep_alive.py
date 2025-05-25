from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080) # Or 80 for Render default if you change it later

def keep_alive():
    t = Thread(target=run)
    t.start()