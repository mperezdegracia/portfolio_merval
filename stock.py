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
    
    def get_day(self,date):
        day = self.data[self.data.index == date]
        if day.empty:
            return None
        return day.values[0]
    


if __name__ == "__main__":
    for symbol in ['GLOB']:
        try:
            stock = Stock(symbol, datetime.date(2023,1,1))
           
        except ValueError:
            print("Invalid symbol or date")

            stock = None

        if stock is not None:
            yesterday= datetime.date.today() - datetime.timedelta(days=1)
            print("Here")
            for i in range(1,20):
                day = stock.get_day((datetime.date(2023,12,8) - datetime.timedelta(days=i)).strftime("%Y-%m-%d") )
                print(day)
            print(day)
