import pickle
import os
import yfinance as yf
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Initialize the MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))
# Load the trained model
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the model
model_path = os.path.join(base_dir, 'model', 'model.pkl')

with open(model_path, 'rb') as file:
    model = pickle.load(file)

# Fetch the stock quote based on user input
def get_stock_data(stock_ticker, start_date, end_date):
    # Download the stock data from Yahoo Finance
    stock_data = yf.download(stock_ticker, start=start_date, end=end_date)
    stock_data.columns = stock_data.columns.get_level_values(0)  # Flatten the columns

    # Create a new dataframe with only the 'Close' column
    new_df = stock_data.filter(['Close'])

    # Fit the scaler on the 'Close' price data
    scaler.fit(new_df)

    return new_df

def predict_stock_price(last_60_days):
    # Scale the data to be between 0 and 1
    last_60_days_scaled = scaler.transform(last_60_days)

    # Create an empty list to store the data
    X_test = []

    # Append the last 60 days of scaled data
    X_test.append(last_60_days_scaled)

    # Convert the data to a numpy array
    X_test = np.array(X_test)

    # Reshape the data for the LSTM model
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    # Get the predicted scaled price
    pred_price = model.predict(X_test)

    # Undo the scaling to get the predicted price
    pred_price = scaler.inverse_transform(pred_price)

    return pred_price

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_ticker = "AAPL"  # Default stock ticker
    start_date = "2012-01-01"  # Default start date
    end_date = "2024-11-15"  # Default end date
    actual_price = None
    predicted_price = None

    if request.method == 'POST':
        stock_ticker = request.form['stock_ticker']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Get the stock data based on the input
        new_df = get_stock_data(stock_ticker, start_date, end_date)

        # Get the last 60 days of closing prices
        last_60_days = new_df[-60:].values

        # Get the prediction for the next day's closing price
        predicted_price = predict_stock_price(last_60_days)

        # Get the actual closing price of the last day (end date)
        actual_price = new_df[-1:].iloc[0, 0]

    # Define the HTML template string
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Price Prediction</title>
    </head>
    <body>
        <h1>Stock Price Prediction</h1>
        
        <!-- Form to input stock ticker, start date, and end date -->
        <form method="POST">
            <label for="stock_ticker">Stock Ticker (e.g., AAPL, TSLA, etc.):</label>
            <input type="text" id="stock_ticker" name="stock_ticker" value="{{ stock_ticker }}">
            <br><br>
            <label for="start_date">Start Date (YYYY-MM-DD):</label>
            <input type="text" id="start_date" name="start_date" value="{{ start_date }}">
            <br><br>
            <label for="end_date">End Date (YYYY-MM-DD):</label>
            <input type="text" id="end_date" name="end_date" value="{{ end_date }}">
            <br><br>
            <input type="submit" value="Get Prediction">
        </form>
        
        {% if actual_price is not none %}
        <p><strong>Actual Closing Price (Last Date):</strong> ${{ actual_price }}</p>
        {% endif %}
        
        {% if predicted_price is not none %}
        <p><strong>Predicted Closing Price (Next Date):</strong> ${{ predicted_price[0][0] }}</p>
        {% endif %}
    </body>
    </html>
    """

    # Render the template with dynamic values
    return render_template_string(html_template, actual_price=actual_price, 
                                  predicted_price=predicted_price, 
                                  stock_ticker=stock_ticker, start_date=start_date, 
                                  end_date=end_date)

if __name__ == '__main__':
    app.run(debug=True)
