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
            self.winter_limit = self.calc_winter_limit()
        self.split_winter_consumption()

    def group_data(self):
        data=pd.DataFrame(self.data)
        data['date']=data['tstp'].dt.date.apply(lambda dt: dt.replace(day=1))
        monthly_data=data.groupby(['date']).sum().reset_index()
        monthly_data.rename(columns={'date':'month','energy(kWh/hh)':'energy'},inplace=True)
        monthly_data['month']=pd.to_datetime(monthly_data['month'])
        monthly_data['mm']=monthly_data['month'].dt.month
        return monthly_data

    def calc_winter_limit(self):
        limit=self.monthly_data[~((self.monthly_data['mm']>3) & (self.monthly_data['mm']<10))]['energy'].mean()
        return max(1.2*limit,430)
        
    def split_winter_consumption(self):
        self.monthly_data['mm']=pd.to_datetime(self.monthly_data['month']).dt.month
        self.monthly_data[['normal_consumption','over_consumption']]=self.monthly_data.apply(lambda x: self.limit_split(x['energy'],self.winter_limit,(x['mm']>3) & (x['mm']<10)), axis=1).apply(pd.Series)

    def price(self):
        out_df=self.monthly_data.copy()[['month']]
        out_df['cfm']=self.params['cfm']
        for col in ['csp', 'tr']:
            out_df[col]=self.monthly_data['energy']*self.params[col]
        for col in ['en', 'pw', 'bpw']:
            out_df[col]=self.monthly_data['normal_consumption']*self.params[col]
        for col in ['pw_win', 'bpw_win']:
            out_df[col]=self.monthly_data['over_consumption']*self.params[col]
        out_df['Total']=out_df[['cfm', 'csp', 'tr', 'en', 'pw', 'bpw']].sum(axis=1)
        return out_df

    @staticmethod
    def limit_split(energy,limit,valid_month=True):
        over_consumption=max(0,energy-limit) if valid_month else 0
        normal_energy = energy if over_consumption==0 else limit
        return (normal_energy,over_consumption)

class BT4_3(Tariff):
    """
    Applies bt4.3 tariff to energy and power array. 
    Params consist in a dict where each param contains a list of values corresponding to each month.
    cfm: "cargo fijo mensual" 
    csp: "cargo por servicio público"
    tr: "Transporte de electricidad"
    en: "Cargo por energía"
    ppw: "Cargo por demanda máxima de potencia suministrada"
    ppw_ph: "Cargo por demanda máxima de potencia leída en horas de punta"

    ppw_ph
    - Durante los meses que contengan horas de punta, se aplicará el precio unitario correspondiente
    a la demanda máxima de potencia en horas de punta efectivamente leída en cada mes.
    - Durante los meses que no contengan horas de punta se aplicará el precio unitario correspondiente
    al promedio de las dos mayores demandas máximas de potencia en horas de punta, registradas
    durante los meses del período de punta inmediatamente anterior.

    ppw
    - El cargo mensual por demanda máxima de potencia suministrada de la tarifa BT4.3 se facturará
    aplicando el precio unitario correspondiente, al promedio de las dos más altas demandas máximas de
    potencia registradas en los últimos 12 meses, incluido el mes que se facture.
    """

    def __init__(self, data, params,winter_limit=0) -> None:
        super().__init__(data, params)
        self.data_expand=self.prepare_data()

    def prepare_data(self):
        data2=self.data.copy()
        data2['power']=data2['energy(kWh/hh)']/2
        data2['date']=data2['tstp'].dt.date.apply(lambda dt: dt.replace(day=1))
        data2['mm']=data2['tstp'].dt.month
        data2['ph_months']=data2['mm'].between(4,9)
        data2['ph']=((data2['tstp'].dt.hour.between(18,22)) & (data2['ph_months']))
        return data2
        
