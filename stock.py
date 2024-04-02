import datetime 
import yfinance as yf
import pandas as pd


class Stock:
    def __init__(self, symbol, date) -> None:
        self.symbol = symbol + ".BA"
        self.symbol = self.symbol.strip()
        self.data = yf.download(self.symbol,date)['Adj Close']
        if self.data.empty:
            raise ValueError("Invalid symbol or date")       

    def get(self, start, end=datetime.date.today().strftime("%Y-%m-%d")):
        return self.data[(self.data.index >= start) & (self.data.index <= end)]
    
    def get_last(self):
        return self.get_last_rec(datetime.date.today())
    
    def get_last_rec(self, date):
        price = self.get_day(date.strftime("%Y-%m-%d"))
        if price is not None:
            return price    
        return self.get_last_rec(date - datetime.timedelta(days=1))
    

    def get_day(self,date):
        day = self.data[self.data.index == date]
        if day.empty:
            return None
        return day.values[0]
    


if __name__ == "__main__":

    stock = Stock("GGAL", datetime.date(2023,1,1))

    print(stock.get_last())
   