from flask import Flask, jsonify
import websocket
import threading
import json
from flask_cors import CORS  # Import CORS
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})  # Enable CORS for specific origin

data_responses = []  # List to store processed WebSocket messages
stop_thread = False  # Flag to stop the background thread when needed

def on_message(ws, message):
    # Parse the message and process it
    parsed_message = json.loads(message)

    # Remove the "c" field and only keep one data point
    if "data" in parsed_message:
        for item in parsed_message["data"]:
            item.pop("c", None)  # Remove "c" field if present

        # Optionally keep only the first entry in "data"
        if parsed_message["data"]:
            data_responses.clear()  # Clear previous data to keep latest
            data_responses.append({
                "data": [parsed_message["data"][0]],  # Only the first entry
                "type": parsed_message["type"]
            })

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws):
    print("WebSocket closed")

def on_open(ws):
    # Send subscription messages
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    ws.send('{"type":"subscribe","symbol":"ETH/USDT"}')
    ws.send('{"type":"subscribe","symbol":"LTC"}')

def start_websocket():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://ws.finnhub.io?token=cssart9r01qld5m1bar0cssart9r01qld5m1barg",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()

def collect_data_periodically():
    global stop_thread
    while not stop_thread:
        # Collect data every 10 seconds
        time.sleep(10)
        # Process data here (optional based on new WebSocket messages)
        # For now, we'll just ensure we always fetch the latest WebSocket message.
        if data_responses:
            print(f"Data collected: {data_responses[0]}")
        else:
            print("No data yet collected.")

# Start the WebSocket connection in a separate thread
threading.Thread(target=start_websocket).start()

# Start the periodic data collection in another background thread
threading.Thread(target=collect_data_periodically, daemon=True).start()

@app.route("/data", methods=["GET"])
def get_data():
    # Return the latest data response as JSON
    return jsonify(data_responses[0] if data_responses else {})

if __name__ == "__main__":
    app.run(debug=True)
