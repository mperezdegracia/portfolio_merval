import requests
import pandas as pd
import datetime



class USD:
    BASE_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/?casa=bolsa"
    def __init__(self) -> None:
        response = requests.get(USD.BASE_URL)
        self.df = pd.DataFrame(response.json())
        self.df = self.df.rename(columns={'fecha': 'date'})
        self.df["rate"] = (self.df["compra"] + self.df["venta"]) / 2
        self.df = self.df.drop(columns=["casa", "compra","venta"])
        self.df['date'] = pd.to_datetime(self.df['date'], format='%Y-%m-%d')

    def get(self, start, end=datetime.date.today().strftime("%Y-%m-%d")):
        # return only the rows between the dates
        start = start.strftime("%Y-%m-%d")
        period = self.df[(self.df['date'] >= start) & (self.df['date'] <= end)]
        return period        

    def get_day(self, date):
        date = pd.to_datetime(date).strftime("%Y-%m-%d")  # ensure date is in the correct format
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        # if date is after yesterday :
        if date >= yesterday:
            date = yesterday
        day = self.df[self.df['date'] == date]
        if day['rate'].empty:
            print("Error getting USD value !!")
            
            return None
        usd_value = day['rate'].values[0]
        return usd_value
    @classmethod
    def get_last(cls):
        return USD._get_day(datetime.date.today()- datetime.timedelta(days=1))
    # class method to get specific date value
    @classmethod
    def _get_day(cls,date):
        # format from "Y-M-D" to "Y/M/D"

        date = str(date).replace("-","/")
        response = requests.get(f"https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa/{date}")

        if response.status_code != 200:
            return None
        res = response.json()
        rate = (res["compra"] + res["venta"]) / 2
        return rate


if __name__ == "__main__":

    usd_ = USD()
    #yesterday = datetime.date.today() - datetime.timedelta(days=1)
    #price = usd_.get_day(yesterday)
    print(USD.get_last())