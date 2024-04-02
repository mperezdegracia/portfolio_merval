import pandas as pd

class BrokerParser:
    def __init__(self):
        pass

    def parse(self, file_path):
        raise NotImplementedError("parse method is not implemented")
    
class CocosParser(BrokerParser):
    def __init__(self):
        self.df = None
        self.fee = 0
        

    def parse(self, file_path):
        print("Parsing Cocos file: ", file_path)

        self.df = pd.read_csv(file_path, sep=',', header=0, skiprows=7)
        # remove rows with NaN in Comprobante
        self.df = self.df.dropna(subset=['Comprobante'])
        # leave only  this columns: ["Fecha Liquidación","Comprobante","Ticker","Cantidad","Precio","Importe Pesos"]
        self.df = self.df[["Fecha Liquidación","Comprobante","Ticker","Cantidad","Precio"]]       
        # rename Comprobante to Tipo
        self.df = self.df.rename(columns={"Comprobante": "Tipo"})

        self.df = self.df[self.df["Tipo"].str.contains("CPRA|VENTA")]
        self.df.reset_index(drop=True, inplace=True)
        # do the same to price
        self.df["Precio"] = self.df["Precio"].str.replace('.', '')
        self.df["Precio"] = self.df["Precio"].str.replace(',', '.').astype(float).abs()
        # do the same to Cantidad
        self.df["Cantidad"] = self.df["Cantidad"].str.replace('.', '.')
        self.df["Cantidad"] = self.df["Cantidad"].str.replace(',', '.').astype(float).abs()
        # turn into int
        # turn date into dd/mm/yyyy
        self.df["Fecha Liquidación"] = pd.to_datetime(self.df["Fecha Liquidación"],dayfirst=True).dt.strftime('%d/%m/%Y')
        self.df["fee"] = self.df["Precio"].astype(float) * self.df["Cantidad"].astype(int) * self.fee
        self.df = self.df.rename(columns={"Fecha Liquidación": "date", "Tipo":"op", "Cantidad":"qty", "Precio":"price", "Ticker":"symbol"})

        return self.df
    
class InviuParser(BrokerParser):

    def __init__(self):
        self.df = None
        self.fee = 0.006
        

    def parse(self, file_path):
        print("Parsing Inviu file: ", file_path)

        self.df = pd.read_csv(file_path, sep=',', header=0, skiprows=6)
        # remove rows with NaN in Comprobante

        self.df = self.df.dropna(subset=["Fecha de Liquidación","Descripción","Tipo de Operación","Ticker","Cantidad VN","Precio","Import Bruto","Importe Neto","Saldo"])
        # clean balance rows
        #apply strip to all columns
        self.df = self.df[~self.df['Descripción'].str.contains("Saldo", na=False)]
        self.df = self.df.rename(columns={"Fecha de Liquidación": "Fecha Liquidación", "Cantidad VN":"Cantidad","Tipo de Operación": "Tipo"})
        self.df["Fecha Liquidación"] = pd.to_datetime(self.df["Fecha Liquidación"], dayfirst=True).dt.strftime('%d/%m/%Y')
        
        self.df = self.df[["Fecha Liquidación","Tipo","Ticker","Descripción","Cantidad","Precio"]]
        # apply strip to Ticker and Tipo
        self.df["Ticker"] = self.df["Ticker"].str.strip()

        self.df["Tipo"] = self.df["Tipo"].str.strip()

        self.not_ops = self.df[~self.df["Tipo"].str.contains("CPRA|VENTA")]

        self.ops = self.df[self.df["Tipo"].str.contains("CPRA|VENTA")]
        
        self.dividends = self.not_ops[self.not_ops["Descripción"].str.contains("Dividendo en acciones")]
        self.reval = self.not_ops[self.not_ops["Descripción"].str.contains("Revalúo en acciones") ]

        for i,row in self.reval.iterrows():
            symbol = row["Descripción"].strip().replace("Revalúo en acciones / ","")
            qty = row["Cantidad"]
            price = row["Precio"]
            date = row["Fecha Liquidación"]
            new_row = pd.DataFrame([{"Fecha Liquidación":date,"Tipo":"CPRA","Ticker":symbol,"Cantidad":qty,"Precio":price}])
            self.ops = self.ops[~((self.ops["Ticker"] == symbol) & (self.ops["Fecha Liquidación"] < date) & (self.ops["Tipo"] == "CPRA"))]
            self.ops = pd.concat([self.ops, new_row]) 
        for i,row in self.dividends.iterrows():
            symbol = row["Descripción"].strip().replace("Dividendo en acciones / ","")
            qty = row["Cantidad"]
            date = row["Fecha Liquidación"]
            self.ops = pd.concat([self.ops, pd.DataFrame([{"Fecha Liquidación":date,"Tipo":"CPRA","Ticker":symbol,"Cantidad":qty,"Precio":0}])])
        
        
        
        self.ops.reset_index(drop=True, inplace=True)
        # # exclude Descripcion
        self.ops = self.ops.drop(columns=["Descripción"])
        self.ops = self.ops[["Fecha Liquidación","Tipo","Ticker","Cantidad","Precio"]]

        # turn date into dd/mm/yyyy
        self.ops["Fecha Liquidación"] = self.ops["Fecha Liquidación"]

        self.ops["Precio"] = self.ops["Precio"].astype(float)
        self.ops["Cantidad"] = self.ops["Cantidad"].astype(int)
        self.ops["fee"] = self.ops["Precio"] * self.ops["Cantidad"] * self.fee
        # rename columns to 'date', 'op', 'qty', 'price', "fee"
        self.ops = self.ops.rename(columns={"Fecha Liquidación": "date", "Tipo":"op", "Cantidad":"qty", "Precio":"price", "Ticker":"symbol"})
        return self.ops