
from usd import USD
from stock import Stock
import datetime
import pandas as pd


class Position:
    
        def __init__(self, df, symbol, usd: USD = None) -> None:

            # init position variables with None
            self.avg_price = None
            self.qty = 0
            self.symbol = None
            self.buys = None
            self.sells = None
            self.stock = None
            self.usd = usd



            self.symbol = symbol
            self.data = df.sort_values(by='date')            
            self.parse()
            self.set_stock()
            #self.to_usd()

        
        def error_earning_df(self, buy=0, sell=0, earning=0, p=0):
            return pd.DataFrame({"symbol": self.symbol ,"buys": round(buy,2), "sells": round(sell,2), "earnings": round(earning,2), "%": round(p,2)}, index=[0])
        def set_stock(self):
            # minimum buy date
            date = self.buys['date'].min()
            try:
                self.stock = Stock(self.symbol, date)
            except ValueError:
                print(f"Stock {self.symbol} not found")
                self.stock = None



        def check_stock(self):
            if self.stock is None:
                print(f"ERROR Can't perform operarion: Stock {self.symbol} not found")
                return False
            return True
        

        def get(self):
            return {"symbol": self.symbol, "qty": self.qty, "avg_price": self.avg_price} 
        
        def parse(self):
            
            self.buys = self.data[self.data['op'] == 'BUY']
            self.sells = self.data[self.data['op'] == 'SELL']

            # sells has negative qty, fix
            self.sells['qty'] = self.sells['qty'].abs()
            self.qty = self.buys['qty'].sum() - self.sells['qty'].sum()

            self.to_usd()


        def earnings_ars(self):
            # returns a df with the positions earnings in ARS

            buys = self.buys['price'] * self.buys['qty']
            sells = self.sells['price'] * self.sells['qty']

            # if no sells or buys should be 0

            buys = buys.sum()   
            sells = sells.sum()
            current_pos = self.valuation()

            if current_pos is None:
                return self.error_earning_df(buy=buys, sell=sells)
            
            total_val = sells + current_pos if current_pos is not None else sells
            earning = total_val - buys
            earning_p = (total_val / buys - 1) * 100 if buys != 0 else 0
            # df with initial position valuation, current position valuation and ratio %
            df = pd.DataFrame({"symbol": self.symbol ,"buys": round(buys,2), "sells": round(total_val,2), "earnings": round(earning,2), "%": round(earning_p,2)}, index=[0])
            
            return df
        



        def earnings_usd(self):
            # returns a df with the positions earnings in USD
            

            # return Error if usd_price column is not present
            if 'usd_price' not in self.buys.columns:
                print("USD price not present in buys dataframe")
                return self.error_earning_df()
            

            buys = self.buys['usd_price'] * self.buys['qty']
            sells = self.sells['usd_price'] * self.sells['qty']

            # if no sells or buys should be 0

            buys = buys.sum()   
            sells = sells.sum()
            current_pos = self.valuation_usd()
            
            if current_pos is None:
                return self.error_earning_df(buy=buys, sell=sells)
            
            total_val = sells + current_pos
            earning = total_val - buys
            earning_p = (total_val / buys  - 1) * 100 if buys != 0 else 0
            # df with initial position valuation, current position valuation and ratio %
            df = pd.DataFrame({"symbol": self.symbol ,"buys": round(buys,2), "sells": round(total_val,2), "earnings": round(earning,2), "%": round(earning_p,2)}, index=[0])
            
            return df
        
        
        def todays_price(self):
            if not self.check_stock():
                return None

            date = (datetime.date.today() - datetime.timedelta(days=1)) if self.qty != 0 else self.sells['date'].max()
            actual_price = self.stock.get_day(date.strftime("%Y-%m-%d"))
            if actual_price is None:
                print(f"Stock {self.symbol} not found")
                return None
            return actual_price
        
        def get_usd(self, date):
            if self.usd is None:
                return USD._get_day(date)
            else:
                return self.usd.get_day(date)
            
        def valuation(self) :
            # returns valuation of all remaining stocks in ARS
            actual_price = self.todays_price()
            if actual_price is None:
                return None
            return actual_price * self.qty 
        
        def valuation_usd(self):
            # returns valuation of all remaining stocks in USD
            if not self.check_stock():
                return None
            
            actual_price = self.todays_price()
            if actual_price is None:
                return None
            
            actual_usd = self.get_usd((datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
            return actual_price / actual_usd * abs(self.qty) 
        def to_usd(self):
            self.buys.loc[:, 'usd'] = self.buys['date'].dt.strftime('%Y-%m-%d').apply(lambda x: self.get_usd(x))
            self.sells.loc[:, 'usd'] = self.sells['date'].dt.strftime('%Y-%m-%d').apply(lambda x: self.get_usd(x))
            self.buys.loc[:, 'usd_price'] = self.buys['price'] / self.buys['usd']
            self.sells.loc[:, 'usd_price'] = self.sells['price'] / self.sells['usd']

            self.avg_price =  (self.buys['usd_price'] * self.buys['qty'] / self.buys['qty'].sum()).sum()

        def earnings(self):
            #calculate the earnings of the position

            actual_price = self.todays_price()
            date = (datetime.date.today() - datetime.timedelta(days=1)) if self.qty != 0 else self.sells['date'].max()

            actual_usd = self.get_usd(date.strftime("%Y-%m-%d"))
            
            actual_price_usd = actual_price / actual_usd
            return ((actual_price_usd - self.avg_price) / self.avg_price) * 100

            
        def reval(self, data):
            data["op"] = "BUY"
            reval_row = data
            reval_date = pd.to_datetime(reval_row['date'])
            self.data = self.data[((self.data['date'] > reval_date) & (self.data['op'] == 'BUY')) | (self.data['op'] == 'SELL')]
            # Append a new row with the revaluation data
            self.data = self.data._append(reval_row, ignore_index=True).sort_values(by='date')
            self.parse()

            


class Portfolio: # base

    
    def __init__(self,df) -> None:
        self.df = df
        self.positions = {}
        self.comission = None
        self.parse()

    
    def get(self):
        l = []
        for symbol, position in self.positions.items():
            l.append(position.get())
        return pd.DataFrame(l)
    

    def __str__(self):
        return self.get().__str__()
    def parse(self):
        raise NotImplementedError()
    

    def current_val(self):

        val = 0
        for symbol, position in self.positions.items():
            current = position.valuation()
            val += current if current is not None else 0
        return val
    
    def current_val_usd(self):

        val = 0
        for symbol, position in self.positions.items():
            current = position.valuation_usd()
            val += current if current is not None else 0
        return val
    def stats_ars(self):
        # returns df with the valuation of the portfolio
        df = pd.DataFrame()
        for position in self.positions.values():
            df = pd.concat([df, position.earnings_ars()])
        # print to csv
            
        tot_buys = df['buys'].sum()
        tot_sells = df['sells'].sum()
        tot_earnings = df['earnings'].sum()
        valuation = self.current_val()
        tot_p = (tot_earnings / valuation) * 100 if tot_buys != 0 else 0

        total = pd.DataFrame({"symbol": "TOTAL", "buys": round(tot_buys,2), "sells": round(tot_sells,2), "earnings": round(tot_earnings,2), "%": round(tot_p,2)}, index=[0])
        
        df = pd.concat([df, total])

        #pretty print to csv, so its aligned

        df.to_csv("portfolio_stats_ars.csv")
        
        # Convert the DataFrame to a string with aligned columns
        df_str = df.to_string()

        # Write the string to a file
        with open("portfolio_stats_ars_pretty.csv", "w") as f:
            f.write(df_str)


        return df
    def stats_usd(self):
        df = pd.DataFrame()
        for position in self.positions.values():
            df = pd.concat([df, position.earnings_usd()])

        tot_buys = df['buys'].sum()
        tot_sells = df['sells'].sum()
        tot_earnings = df['earnings'].sum()
        valuation = self.current_val_usd()
        tot_p = (tot_earnings / valuation ) * 100 if tot_buys != 0 else 0

        total = pd.DataFrame({"symbol": "TOTAL", "buys": round(tot_buys,2), "sells": round(tot_sells,2), "earnings": round(tot_earnings,2), "%": round(tot_p,2)}, index=[0])
        
        df = pd.concat([df, total])

        # calculate comissions
        #comissions = (total['buys'].sum()  + total['sells'] ) * self.comission

        # print to csv
        df.to_csv("portfolio_stats_usd.csv")

        # Convert the DataFrame to a string with aligned columns
        df_str = df.to_string()

        # Write the string to a file
        with open("portfolio_stats_usd_pretty.csv", "w") as f:
            f.write(df_str)
        return df
    

    def df_valuations_usd(self):
        # returns the valuation of the portfolio
        df = pd.DataFrame() # df symbol,valuation
        for symbol, position in self.positions.items():
            valuation = position.valuation_usd()
            if valuation is not None:
                df = pd.concat([df, pd.DataFrame({"symbol": symbol, "valuation": valuation}, index=[0])])

        return df
    
    def df_valuations_ars(self):
        # returns the valuation of the portfolio
        df = pd.DataFrame() # df symbol,valuation
        # total is df's last row, with the sum of all buys, sells, earnings, % valuation, symbol = "TOTAL",
        
        for symbol, position in self.positions.items():
            
            valuation = position.valuation()
            if valuation is not None:
                df = pd.concat([df, pd.DataFrame({"symbol": symbol, "valuation": round(valuation,2)}, index=[0])])
        
        return df

    def chart(self):
        # data is a df with the columns symbol, buys, sells, earnings, %

        import matplotlib.pyplot as plt
        import numpy as np

        vals = self.valuation_ars()
        # filter out the symbols with None valuation
        # if position < 0 then filter out vals
        # vals is df
        vals = vals[vals['valuation'] > 0]
        symbols = vals['symbol']
        position = vals['valuation']

        fig, ax = plt.subplots()
        ax.pie(position, labels=symbols, autopct='%1.1f%%')
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.show()

        # save as image
        fig.savefig("portfolio_chart.png")

    
class InviuPortfolio(Portfolio):

    def __init__(self,df) -> None:
        self.usd = USD()
        super().__init__(df)
        self.comission = 0.006
    def parse(self):
        # adapt the dataset
        # clean rows with empty values
        self.df = self.df.dropna(subset=["Fecha de Liquidación","Descripción","Tipo de Operación","Ticker","Cantidad VN","Precio","Import Bruto","Importe Neto","Saldo"])
        # clean balance rows
        self.df = self.df[~self.df['Descripción'].str.contains("Saldo", na=False)]



        grouped_df = self.df.groupby("Ticker")[["Descripción","Fecha de Liquidación","Tipo de Operación","Cantidad VN", "Precio"]]
        revals = {}
        for symbol, position in grouped_df:
            symbol = symbol.strip()
            position = position.set_axis(['desc', 'date', 'op', 'qty', 'price'], axis=1)
            position['date'] = pd.to_datetime(position['date'], format='%d/%m/%Y')
            position['price'] = pd.to_numeric(position['price'], errors='coerce')
            position['qty'] = pd.to_numeric(position['qty'], errors='coerce')

            if position['op'].str.contains("Dividendo en acciones").any():
               # replace operation with BUY and price with 0 for that specific row
                position.loc[position['op'] == "Dividendo en acciones", 'price'] = 0
                position.loc[position['op'] == "Dividendo en acciones", 'op'] = "BUY"

            if symbol != "-":


                position['op'] = position['op'].replace({'CPRA': 'BUY', 'VENTA': 'SELL'})
                position = position.drop(columns=['desc'])
                self.positions[symbol]= Position(position, symbol, self.usd)
                
            else:
                
                for reval in position.to_dict(orient="records"):
                    
                    symbol = reval["desc"].replace("Revalúo en acciones / ", "")
                    revals[symbol] = {"qty":reval["qty"], "price":reval["price"], "date":reval["date"]}


        for reval_symbol, reval_position in revals.items():
            self.positions[reval_symbol].reval(reval_position)


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True
    FILENAME = "inviu-voucher -2024-03-26T02_23_28.406Z.csv"
    #FILENAME = "inviu-voucher -2024-03-06T13_56_18.484Z.csv"
    df = pd.read_csv(FILENAME, skiprows=6)
    portfolio = InviuPortfolio(df)

    

    data_ars = portfolio.stats_ars()
    data_usd = portfolio.stats_usd()
    # total = data_ars.iloc[-1] 
    # comissions = round((total['buys'] + total['sells']) * portfolio.comission, 2)


    print(data_ars)
    print(data_usd)
    # portfolio.chart()
    # # get the last row of data_ars df


    # print("Total comissions: ", comissions)