from flask import Flask, jsonify, request, render_template_string, Response
from flask_cors import CORS  # Import CORS
import yfinance as yf
import pandas as pd
import time
from datetime import date
import matplotlib
import matplotlib.pyplot as plt
import io
import numpy as np
import pickle
import os
import math
from sklearn.preprocessing import MinMaxScaler
import websocket
import threading
import json

matplotlib.use('Agg')  # Set the matplotlib backend to 'agg'

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})  # Enable CORS for specific origin

# ---------------- Stock Prediction App Variables ----------------
scaler = MinMaxScaler(feature_range=(0, 1))
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'model', 'svm.pkl')  # now we use svm.pkl

with open(model_path, 'rb') as file:
    model = pickle.load(file)  # Changed back to model.pkl

symbol = "META"  # Default stock symbol

# ---------------- WebSocket App Variables ----------------
data_responses = []  # List to store processed WebSocket messages
stop_thread = False  # Flag to stop the background thread when needed

def fetch_stock_data(symbol, start, end, retries=3, delay=5):
    """Fetch stock data with retry logic."""
    for attempt in range(retries):
        try:
            stock_data = yf.download(symbol, start=start, end=end)
            stock_data.reset_index(inplace=True)
            stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
            return stock_data
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    return None

# ---------------- WebSocket Functions ----------------
def on_message(ws, message):
    parsed_message = json.loads(message)
    if "data" in parsed_message:
        for item in parsed_message["data"]:
            item.pop("c", None)  # Remove "c" field if present
        if parsed_message["data"]:
            data_responses.clear()
            data_responses.append({
                "data": [parsed_message["data"][0]],  # Only the first entry
                "type": parsed_message["type"]
            })

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws):
    print("WebSocket closed")

def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    ws.send('{"type":"subscribe","symbol":"ETH-USD"}')
    ws.send('{"type":"subscribe","symbol":"LTC-USD"}')

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
        time.sleep(10)
        if data_responses:
            print(f"Data collected: {data_responses[0]}")
        else:
            print("No data yet collected.")

threading.Thread(target=start_websocket).start()
threading.Thread(target=collect_data_periodically, daemon=True).start()

# ---------------- Flask Routes ----------------
@app.route("/", methods=["GET", "POST"])
def hello_world():
    global symbol
    if request.method == "POST":
        symbol = request.form.get("symbol", "No symbol provided")
    return render_template_string(
        """
        <form method="post">
            <h1>Stocks</h1>
            <input type="text" name="symbol" value="{{ symbol }}" />
            <button type="submit">Submit</button>
        </form>
        """, symbol=symbol
    )

@app.route("/get_stock_data", methods=["POST"])
def get_stock_data():
    global symbol
    request_data = request.get_json()
    stock_symbol = request_data.get("symbol", symbol)
    start_date = '2015-01-01'
    end_date = date.today()
    stock_data = fetch_stock_data(stock_symbol, start_date, end_date)
    if stock_data is not None:
        stock_data.columns = [str(col) for col in stock_data.columns]
        return jsonify(stock_data.to_dict(orient="records"))
    else:
        return jsonify({"error": "Failed to retrieve stock data"}), 500

@app.route("/predictions", methods=["POST"])
def get_predictions_data():
    request_data = request.get_json()
    stock_symbol = request_data.get("symbol", "META")
    start_date = request_data.get("start_date", '2015-01-01')
    end_date = request_data.get("end_date", str(date.today()))
    df = fetch_stock_data(stock_symbol, start_date, end_date)
    if df is None:
        return jsonify({"error": "Failed to retrieve stock data"}), 500
    
    # Create predictor variables
    df['Open-Close'] = df.Open - df.Close
    df['High-Low'] = df.High - df.Low

    # Store all predictor variables in a variable X
    X = df[['Open-Close', 'High-Low']]
    
    df['Predicted_Signal'] = model.predict(X) # Predict using loaded model
    
    # Calculate daily returns
    df['Return'] = df.Close.pct_change()
    # Calculate strategy returns
    df['Strategy_Return'] = df.Return *df.Predicted_Signal.shift(1)
    # Calculate Cumulutive returns
    df['Cum_Ret'] = df['Return'].cumsum()
    
    # Calculate Cumulative strategy returns
    df['Cum_Strategy'] = df['Strategy_Return'].cumsum()
    
    data = df[['Date', 'Close']].copy()
    
    #Shift the 'Close' prices by 1 day to simulate the prediction and use the prediction to simulate a possible action, if the signal is one then use close and if 0 then use close from the day before
    data['Predictions'] = (df['Close'].shift(1) * (df['Predicted_Signal'])) + (df['Close'].shift(1) * (1 - df['Predicted_Signal']))
    data['Predictions'].fillna(data['Close'], inplace=True)
    return jsonify(data[['Date', 'Close', 'Predictions']].to_dict(orient="records"))


@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(data_responses[0] if data_responses else {})

if __name__ == "__main__":
    app.run(debug=True)