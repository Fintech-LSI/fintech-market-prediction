# Machine learning
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import yfinance as yf # data source (yahoo finance)

# For data manipulation
import pandas as pd
import numpy as np

# To plot
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

# To ignore warnings
import warnings
warnings.filterwarnings("ignore")
# get the stock quote 
df = yf.download('NVDA', start='2020-01-01', end='2024-11-13')

# multi index to one index (ptoblem yfinance.download)
df.columns = df.columns.get_level_values(0)

# show the data 
df

# Create predictor variables
df['Open-Close'] = df.Open - df.Close
df['High-Low'] = df.High - df.Low

# Store all predictor variables in a variable X
X = df[['Open-Close', 'High-Low']]
X.head()

# Target variables
y = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
y

split_percentage = 0.8
split = int(split_percentage*len(df))

# Train data set
X_train = X[:split]
y_train = y[:split]

# Test data set
X_test = X[split:]
y_test = y[split:]


import pickle 

# Support vector classifier
cls = SVC().fit(X_train, y_train)

with open("../model/svm.pkl", 'wb') as file:
    pickle.dump(cls, file)

df['Predicted_Signal'] = cls.predict(X)
# Calculate daily returns
df['Return'] = df.Close.pct_change()
# Calculate strategy returns
df['Strategy_Return'] = df.Return *df.Predicted_Signal.shift(1)
# Calculate Cumulutive returns
df['Cum_Ret'] = df['Return'].cumsum()
df

# Plot Strategy Cumulative returns 
df['Cum_Strategy'] = df['Strategy_Return'].cumsum()
df


import matplotlib.pyplot as plt
 
plt.plot(df['Cum_Ret'],color='red')
plt.plot(df['Cum_Strategy'],color='blue')
