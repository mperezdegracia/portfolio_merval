
from usd import USD
from stock import Stock
import datetime
import pandas as pd
from broker_parser import BrokerParser, CocosParser, InviuParser


class Position:
    def __init__(self, df, symbol) -> None:
        self.df = df
        self.symbol = symbol
        # get min date op 
        min_date = self.df["date"].min()
        try:
            self.stock = Stock(self.symbol, min_date)
        except ValueError:
            print(f"Stock {self.symbol} not found")
            self.stock = None

        self.value_ars = self.position_ars() 
        self.value_usd = self.position_usd()

    def position_ars(self):
        sells = self.df[self.df["op"] == "SELL"]
        qty_sold = sells["qty"].sum()
        buys = self.df[self.df["op"] == "BUY"]
        qty_bought = buys["qty"].sum() 
        position = 0#(sells["price"] * sells["qty"]).sum()
        print(f"{self.symbol} BOUGHT: { (buys['price'] * buys["qty"]).sum()} SOLD POSITION:  {position}", end=" ")
        if qty_sold < qty_bought:
            qty_remaining = qty_bought - qty_sold
            # calculate todays sell price
            last_price = self.manage_stock()

            if last_price == 0: # tomamos el promedio de compra
                position = (buys["price"].sum() / qty_bought) * qty_remaining 
            else: 
                position += qty_remaining * last_price
            print(f"NOT SOLD {qty_remaining} -> VALUE {qty_remaining * last_price}")
        else:
            print("")
        self.value_ars = position

        return position
    def manage_stock(self):
        if self.stock is not None:
            return self.stock.get_last()
        elif self.symbol == "AL30":
            return 544.0
        else:
            return 0


    def position_usd(self):
        value_usd = USD.get_last()
        return self.value_ars / value_usd

    def ars_earnings_df(self):
        sell_rows = self.df[self.df["op"] == "SELL"]
        sells = (sell_rows["price"] * sell_rows["qty"]).sum()

        buy_rows = self.df[self.df["op"] == "BUY"]
        buys = (buy_rows["price"] * buy_rows["qty"]).sum()

        sells += self.value_ars

        earning = sells - buys
        earning_p = (earning / buys) * 100
        return pd.DataFrame({"symbol": self.symbol ,"buys": round(buys,2), "sells": round(sells,2), "earnings": round(earning,2), "%": round(earning_p,2)}, index=[0])
    
    def usd_earnings_df(self):
        sell_rows = self.df[self.df["op"] == "SELL"]
        sells = (sell_rows["price_usd"] * sell_rows["qty"]).sum()

        buy_rows = self.df[self.df["op"] == "BUY"]
        buys = (buy_rows["price_usd"] * buy_rows["qty"]).sum()
        sells += self.value_usd
        earning = sells - buys
        earning_p = (earning / buys) * 100
        return pd.DataFrame({"symbol": self.symbol ,"buys": round(buys,2), "sells": round(sells,2), "earnings": round(earning,2), "%": round(earning_p,2)}, index=[0])
         


class Portfolio: # base

    
    def __init__(self) -> None:
        # date	op	symbol	qty	price	fee
        self.df = pd.DataFrame(columns= ["date","op","symbol","qty","price","fee"])
        self.positions = {}

    def add(self, df):
        self.df = pd.concat([self.df, df])


    def build(self):
        # sort by date
        self.df = self.df.sort_values(by='date')
        self.df["op"] = self.df["op"].replace("CPRA","BUY")
        self.df["op"] = self.df["op"].replace("VENTA","SELL")
        # abs qty
        self.df["qty"] = self.df["qty"].abs()
        self.to_usd()

        grouped_df = self.df.groupby("symbol")
        for name, group in grouped_df:

            print(name)
            print(group)
            self.positions[name] = Position(group, name)
    
    def to_usd(self):

        usd = USD()

        self.df.loc[:, 'usd'] = self.df['date'].dt.strftime('%Y-%m-%d').apply(lambda x: usd.get_day(x))
        self.df.loc[:, 'price_usd'] = self.df['price'] / self.df['usd']


    def get_ars(self):
        # concat all the positions earnings_df
        df = pd.DataFrame()
        # calculate total row
        total= pd.DataFrame({ "symbol":"TOTAL","buys": 0, "sells": 0, "earnings": 0, "%": 0}, index=[0])
        for position in self.positions.values():
            # add to total
            current = position.ars_earnings_df()
            total["buys"] = total["buys"] + current["buys"]
            total["sells"] = total["sells"] + current["sells"]
            df = pd.concat([df, current])
        total["earnings"] = total["sells"] - total["buys"]
        total["%"] = (total["earnings"] / total["buys"]) * 100
        df = pd.concat([df, total])
        
        # print to csv

        df_str = df.to_string()

    #     # Write the string to a file
        with open("portfolio_ars.csv", "w") as f:
            f.write(df_str)
        
        return df
    

    def get_usd(self):
        # concat all the positions earnings_df
        df = pd.DataFrame()
        total= pd.DataFrame({ "symbol":"TOTAL", "buys": 0, "sells": 0, "earnings": 0, "%": 0}, index=[0])


        for position in self.positions.values():
            current =position.usd_earnings_df()
            df = pd.concat([df, current])
            total["buys"] = total["buys"] + current["buys"]
            total["sells"] = total["sells"] + current["sells"]

        total["earnings"] = total["sells"] - total["buys"]
        total["%"] = (total["earnings"] / total["buys"]) * 100
        df = pd.concat([df, total])

        df_str = df.to_string()

    #     # Write the string to a file
        with open("portfolio_usd.csv", "w") as f:
            f.write(df_str)

        return df
    

    def chart(self):
        # data is a df with the columns symbol, buys, sells, earnings, %

        import matplotlib.pyplot as plt
        import numpy as np
        # df with "symbol" and "position_ars" and "position_usd" columns declare with columns
        df = pd.DataFrame(columns=["symbol","position_ars","position_usd"])
        for symbol, position in self.positions.items():
            df = pd.concat([df, pd.DataFrame({"symbol": symbol, "position_ars": position.value_ars, "position_usd": position.value_usd}, index=[0])])
       # filter out the symbols with 0 position
        df = df[df["position_ars"] != 0]
        # filter out the symbols with None valuation
        # if position < 0 then filter out vals
        # vals is df
        symbols = df['symbol']
        position = df['position_ars']


        fig, ax = plt.subplots()
        ax.pie(position, labels=symbols, autopct='%1.1f%%')
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.show()

        # save as image
        fig.savefig("portfolio_chart.png")

   


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True

    file_cocos = "cocos_activity.csv"
    file_inviu = "inviu_activity.csv"
    portfolio = Portfolio()
    df1 = InviuParser().parse(file_inviu)
    df2 = CocosParser().parse(file_cocos)
    df = pd.concat([df1, df2])
    # make date column a datetime object
    
    df["date"] = pd.to_datetime(df["date"],dayfirst=True)
    portfolio.add(df)
    portfolio.build()
    print(portfolio.df)
    # print date column type

    portfolio.get_ars()
    portfolio.get_usd()
    portfolio.chart()
    # data_ars = portfolio.stats_ars()
    # data_usd = portfolio.stats_usd()
    # # total = data_ars.iloc[-1] 
    # # comissions = round((total['buys'] + total['sells']) * portfolio.comission, 2)


    # print(data_ars)
    # print(data_usd)
    # # get the last row of data_ars df


    # print("Total comissions: ", comissions)