import pandas as pd
import numpy as np

class Tariff:
    """
    Base for tariffs. Requires data of a year of energy consumption, composed by an array whose columns are timestamp, energy [kwh]
    """

    #Reminder: show warning if more than one year (important in case of BT1 )

    def __init__(self,data,params) -> None:
        self.data=data
        self.params=params
        self.check_data()
        self.check_params()

    def check_data(self):
        """
        Check if input data is well structured, and convert datatypes if necessary
        """
        pass

    def check_params(self):
        """
        Check if input params is well structured
        """
        pass

class BT1(Tariff):
    """
    Applies bt1 tariff to energy array. 
    Params consist in a dict where each param contains a list of values corresponding to each month.
    cfm: "cargo fijo mensual" 
    csp: "cargo por servicio público"
    tr: "Transporte de electricidad"
    en: "Cargo por energía"
    pw: "Cargo por compras de potencia"
    bpw: "Cargo por potencia base en su componente de distribución"
    pw_win: "Cargo por potencia adicional de invierno en su componente de compras de potencia"
    bpw_win: "Cargo por potencia adicional de invierno en su componente de distribución"
    """
    def __init__(self, data, params,winter_limit=0) -> None:
        super().__init__(data, params)
        self.monthly_data=self.group_data()

        if winter_limit==0:
            self.calc_winter_limit()

    
    def group_data(self):
        data=pd.DataFrame(self.data)
        data['date']=data['tstp'].dt.date.apply(lambda dt: dt.replace(day=1))
        monthly_data=data.groupby(['date']).sum().reset_index()
        return monthly_data

        

    def calc_winter_limit(self):
        pass

    def price(self):
        out_df=self.monthly_data