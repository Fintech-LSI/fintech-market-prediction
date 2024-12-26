from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS  # Import CORS
import yfinance as yf
import pandas as pd
import time
from datetime import date
import matplotlib.pyplot as plt
import io
import numpy as np 
import pickle
import os
import math
from sklearn.preprocessing import MinMaxScaler 

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})  # Enable CORS for specific origin


# Initialize the MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))

# Load the trained model
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'model', 'model.pkl')

with open(model_path, 'rb') as file:
    model = pickle.load(file)

# Global variable to store the default stock symbol
symbol = "META"  # Default stock symbol
dataset = None

@app.route("/", methods=["GET", "POST"])
def hello_world():
    global symbol  # Access the global symbol variable

    if request.method == "POST":
        # Get the symbol value sent from the form
        symbol = request.form.get("symbol", "No symbol provided")

    # Render an HTML form to send the symbol value
    return render_template_string(
        """
        <form method="post">
            <h1>Stocks</h1>
            <input type="text" name="symbol" value="{{ symbol }}" />
            <button type="submit">Submit</button>
        </form>
        """, symbol=symbol
    )

@app.route("/plot_stock_data", methods=["POST"])
def plot_stock_data():
    # Retrieve the stock symbol from the request JSON
    request_data = request.get_json()
    stock_symbol = request_data.get("symbol", "META")  # Default to "META" if no symbol is provided

    # Define the date range for stock data
    start_date = '2020-01-01'
    end_date = '2024-11-15'

    # Fetch the stock data
    stock_data = fetch_stock_data(stock_symbol, start_date, end_date)
    
    if stock_data is not None:
        # Plot the closing prices over time
        plt.figure(figsize=(10, 5))
        plt.plot(stock_data['Date'], stock_data['Close'], label=f'{stock_symbol} Closing Price')
        plt.xlabel("Date")
        plt.ylabel("Closing Price (USD)")
        plt.title(f"{stock_symbol} Stock Price Over Time")
        plt.legend()
        
        # Convert plot to a PNG image and return as response
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        
        return Response(img, mimetype='image/png')
    else:
        return jsonify({"error": "Failed to retrieve stock data"}), 500


def fetch_stock_data(symbol, start, end, retries=3, delay=5):
    """Fetch stock data with retry logic in case of network/SSL issues."""
    for attempt in range(retries):
        try:
            stock_data = yf.download(symbol, start=start, end=end)
            stock_data.reset_index(inplace=True)

            # Flatten the column names if they are tuples
            stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]

            return stock_data
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    return None

@app.route("/get_stock_data", methods=["POST"])
def get_stock_data():
    global symbol  # Access the global symbol variable

    # Get the stock symbol from the POST request body
    request_data = request.get_json()
    stock_symbol = request_data.get("symbol", symbol)  # Use global symbol if no symbol is provided

    # Define the date range for stock data
    start_date = '2015-01-01'
    end_date = date.today()  # Current date
    
    # Attempt to fetch stock data for the given symbol
    stock_data = fetch_stock_data(stock_symbol, start_date, end_date)
    
    if stock_data is not None:
        # Ensure all column names are strings for JSON compatibility
        stock_data.columns = [str(col) for col in stock_data.columns]
        
        # Convert DataFrame to JSON-friendly format
        stock_data_json = stock_data.to_dict(orient="records")
        
        # Return the JSON response
        return jsonify(stock_data_json)
    else:
        # Return an error message if data retrieval fails
        return jsonify({"error": "Failed to retrieve stock data"}), 500

@app.route("/predictions", methods=["POST"])
def get_predictions_data():
    # Retrieve the request JSON data
    request_data = request.get_json()
    stock_symbol = request_data.get("symbol", "META")  # Default to "META" if no symbol is provided
    start_date = request_data.get("start_date", '2015-01-01')  # Default start date
    end_date = request_data.get("end_date", str(date.today()))  # Default to today's date if not provided
    
    # Fetch the stock data
    df = fetch_stock_data(stock_symbol, start_date, end_date)
    
    if df is None:
        return jsonify({"error": "Failed to retrieve stock data"}), 500
    
    # Use only the 'Close' column for predictions
    data = df[['Date', 'Close']].copy()  # Include the Date column for the response
    
    # Scaling the data
    dataset = data['Close'].values.reshape(-1, 1)
    training_data_len = math.ceil(len(dataset) * 0.8)
    scaled_data = scaler.fit_transform(dataset)
    
    # Prepare test data for prediction
    test_data = scaled_data[training_data_len - 60:, :]
    
    # Create x_test and y_test datasets
    x_test = []
    y_test = dataset[training_data_len:]
    for i in range(60, len(test_data)):
        x_test.append(test_data[i - 60:i, 0])
    
    # Convert x_test to a numpy array and reshape for the model
    x_test = np.array(x_test)
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
    
    # Predict the stock prices using the trained model
    predictions = model.predict(x_test)
    
    # Inverse transform to get original scale
    predictions = scaler.inverse_transform(predictions)
    
    # Split the data into training and validation sets
    train = data[:training_data_len]
    valid = data[training_data_len:].copy()
    
    # Add predictions to the valid DataFrame
    valid['Predictions'] = predictions
    
    # Convert the response to JSON, including Date, Close, and Predictions
    response_data = valid[['Date', 'Close', 'Predictions']].to_dict(orient="records")
    
    # Return the JSON response with date, actual close, and predicted prices
    return jsonify(response_data)

if __name__ == "__main__":
    app.run(debug=True)
