'''
SecurityList class that loads security data
and finds hedge ratio of portolfio, returns
time series, and other useful functions

'''

import quandl
import numpy as np
import pandas as pd
import datetime
import statsmodels.tsa.vector_ar.vecm as jh
import matplotlib.pyplot as plt
import pickle

quandl.ApiConfig.api_key = 'AfS6bPzj1CsRFyYxCcvz'

class SecurityList():

    def __init__(self,tickers):
        self.tickers = tickers
        self.data = pd.DataFrame(columns=self.tickers)
        self.volume = pd.DataFrame(columns=self.tickers)
        self.split = pd.DataFrame(columns=self.tickers)
        self.div = pd.DataFrame(columns=self.tickers)
        self.close = pd.DataFrame(columns=self.tickers)

    def importData(self,data):
        self.data = data

    def downloadQuandl(self,start,end):

        try:
            self.data,self.volume,self.split,self.div,self.close = pickle.load(open('WIKIdata.pickle','rb'))
        except FileNotFoundError:
            def convert_dt(elem):
                return pd.to_datetime(elem).date()
            for sec in self.tickers:
                print("downloading "+sec)
                try:
                    a = quandl.get('WIKI/'+sec, start_date=start,end_date=end)
                    self.data[sec] = a['Adj. Close']
                    self.volume[sec] = a['Volume']
                    self.split[sec] = a['Split Ratio']
                    self.div[sec] = a['Ex-Dividend']
                    self.close[sec] = a['Close']
                    f = np.vectorize(convert_dt)
                    index = f(a.index)
                except:
                    pass
            self.data = self.data.set_index(index)
            self.volume = self.volume.set_index(index)
            self.split = self.split.set_index(index)
            self.div = self.div.set_index(index)
            self.close = self.close.set_index(index)
            pickle.dump((self.data,self.volume,self.split,self.div,self.close),open('WIKIdata.pickle','wb'))
        self.data = self.data.dropna(axis='columns')
        self.volume = self.volume.dropna(axis='columns')
        self.split = self.split.dropna(axis='columns')
        self.div = self.div.dropna(axis='columns')
        self.close = self.close.dropna(axis='columns')
        print(self.data.columns)
        self.data = self.data[self.tickers]
        self.volume = self.volume[self.tickers]
        self.split = self.split[self.tickers]
        self.div = self.div[self.tickers]
        self.close = self.close[self.tickers]

    def genTimeSeries(self):

        '''
        Generate Time Series using johansen test
        '''
        eig = self.genHedgeRatio()
        ts = np.dot(self.data,eig)
        return ts

    def genHedgeRatio(self):

        matrix = self.genMatrix()
        results = jh.coint_johansen(matrix,0,1)
        return results.evec[:,0]

    def genMatrix(self):

        ts_row,ts_col = self.data.shape
        matrix = np.zeros((ts_row,ts_col))
        for i, sec in enumerate(self.data):
            matrix[:,i] = self.data[sec]
        return matrix

    def getVolume(self):
        return self.volume

    def getSplits(self):
        return self.split

    def getDiv(self):
        return self.div

    def getAdjFactors(self):
        temp = self.div.copy()
        temp[temp != 0] = 1
        close = self.close*temp
        adj_factors = self.div+close
        close[close == 0] = 1
        adj_factors /= close
        adj_factors[adj_factors == 0] = 1
        return adj_factors

    def adjSplits(self):
        split = self.split.product()
        eig = self.genHedgeRatio()
        adj = eig/split
        return adj

    def adjDividends(self):
        adj_fact = self.getAdjFactors()
        total_fact = adj_fact.product()
        return total_fact
