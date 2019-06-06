#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 18:22:35 2019

@author: gabrielpundrich
"""
import pandas as pd

from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM


path_env = "/Users/gabrielpundrich/Dropbox/finance_accounting_data_science/mate/"

path_env = path_env+"/ML/LTSM/"





from pandas import read_csv
from datetime import datetime
# load data

def parse(x):
	return datetime.strptime(x, '%Y %m %d %H')

dataset = read_csv(path_env+'raw.csv',  parse_dates = [['year', 'month', 'day', 'hour']], index_col=0, date_parser=parse)
dataset.drop('No', axis=1, inplace=True)

# manually specify column names
dataset.columns = ['pollution', 'dew', 'temp', 'press', 'wnd_dir', 'wnd_spd', 'snow', 'rain']
dataset.index.name = 'date'

# mark all NA values with 0
dataset['pollution'].fillna(0, inplace=True)

# drop the first 24 hours
dataset = dataset[24:]

# summarize first 5 rows
print(dataset.head(5))

# save to file
dataset.to_csv(path_env+'pollution.csv')


from pandas import read_csv
from matplotlib import pyplot
# load dataset
dataset = read_csv(path_env+'pollution.csv', header=0, index_col=0)
values = dataset.values
# specify columns to plot
groups = [0, 1, 2, 3, 5, 6, 7]
i = 1
# plot each column
pyplot.figure()
for group in groups:
	pyplot.subplot(len(groups), 1, i)
	pyplot.plot(values[:, group])
	pyplot.title(dataset.columns[group], y=0.5, loc='right')
	i += 1
pyplot.show()


# convert series to supervised learning

def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = DataFrame(data)
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg

# load dataset
dataset = read_csv(path_env+'pollution.csv', header=0, index_col=0)
values = dataset.values

# integer encode direction (as it is a categorical variable in the 4th column with the direction of the wind - give a number to each category)
encoder = LabelEncoder()
values[:,4] = encoder.fit_transform(values[:,4])

# ensure all data is float
values = values.astype('float32')

# normalize features
scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(values)

# specify the number of lag hours
n_lags_used = 10
n_features = 8

# frame as supervised learning (using 3 hours as input) (basically creates three lags)
reframed = series_to_supervised(scaled, n_lags_used, 1)
print(reframed.shape)

# split into train and test sets
values = reframed.values
n_train_lags_used = 365 * 24
train = values[:n_train_lags_used, :]
test = values[n_train_lags_used:, :]

# split into input and outputs: n_features is pretty much number of vars
n_obs = n_lags_used * n_features



train_X, train_y = train[:, :n_obs], train[:, -n_features]

test_X, test_y = test[:, :n_obs], test[:, -n_features]
print(train_X.shape, len(train_X), train_y.shape)

# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], n_lags_used, n_features))
test_X = test_X.reshape((test_X.shape[0], n_lags_used, n_features))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)



# design network
model = Sequential()
model.add(LSTM(50, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dense(1))
model.compile(loss='mae', optimizer='adam')

# fit network
history = model.fit(train_X, train_y, epochs=50, batch_size=72, validation_data=(test_X, test_y), verbose=2, shuffle=False)

# plot history
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()

# make a prediction
yhat = model.predict(test_X)
test_X = test_X.reshape((test_X.shape[0], n_lags_used*n_features))

# invert scaling for forecast
inv_yhat = concatenate((yhat, test_X[:, -7:]), axis=1)
inv_yhat = scaler.inverse_transform(inv_yhat)
inv_yhat = inv_yhat[:,0]

# invert scaling for actual
test_y = test_y.reshape((len(test_y), 1))
inv_y = concatenate((test_y, test_X[:, -7:]), axis=1)
inv_y = scaler.inverse_transform(inv_y)
inv_y = inv_y[:,0]


# calculate RMSE
rmse = sqrt(mean_squared_error(inv_y, inv_yhat))
print('Test RMSE: %.3f' % rmse)



inv_y


index_test = dataset.index

Data = {'Actual': inv_y, 'Predicted': inv_yhat , 'Dates': index_test[n_train_lags_used+n_lags_used:]}
df = DataFrame(Data)
df.to_csv(path_env+'output.csv')





#
#
#
#train = inv_y
#valid = inv_yhat
#
#
#len(inv_y)
#len(inv_yhat)
#len(index_test[n_train_lags_used+3:])
#
#import matplotlib.pyplot as plt
#%matplotlib inline
#
#plt.plot(inv_y)
#plt.plot(inv_yhat)
#
#
#
#test[:, :n_obs], test[:, -n_features]
#
#
#DataFrame(test[:, :n_obs]).to_csv(path_env+'1.csv')
#DataFrame(test[:, -n_features]).to_csv(path_env+'2.csv')
#
#
#DataFrame(scaled).to_csv(path_env+'1.csv')
#DataFrame(reframed).to_csv(path_env+'2.csv')
#
#
#
#
#reframed.head(5)
#
#
#scaled
#print(reframed.shape)
#
#
#
#
#




