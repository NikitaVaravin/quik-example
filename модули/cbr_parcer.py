import pandas as pd
import requests as rq
import json
import datetime
import numpy as np

def gather_table(url,start,end,tail = ""):
    
    start_in = datetime.datetime.strptime(start,"%Y-%m-%d").strftime("%d.%m.%Y")
    end_in = datetime.datetime.strptime(end,"%Y-%m-%d").strftime("%d.%m.%Y")
        
    cbr_eff_rate = pd.read_html(url + start_in + "&UniDbQuery.To=" + end_in + tail)
    cbr_eff_rate = cbr_eff_rate[0]
        
    return cbr_eff_rate

def gather_ruonia(start,end):

    cbr_eff_rate = gather_table("https://www.cbr.ru/hd_base/ruonia/dynamics/?UniDbQuery.Posted=True&UniDbQuery.From=",start,end)

    cbr_eff_rate["Дата ставки"] = cbr_eff_rate["Дата ставки"].apply(lambda x : datetime.datetime.strptime(x,"%d.%m.%Y"))
    cbr_eff_rate["Ставка RUONIA, %"] = cbr_eff_rate["Ставка RUONIA, %"]/10000

    cbr_eff_rate = cbr_eff_rate.rename(columns = {"Дата ставки":"Date","Ставка RUONIA, %":"ruonia"}).loc[:,["Date","ruonia"]]

    return cbr_eff_rate

def get_cbr_swap(start,end,cur):
    
    if cur == "USD":
        cur_in = 0
    elif cur == "EUR":
        cur_in = 1
    elif cur == "CNY":
        cur_in = 2
        
    operation_df = gather_table("https://www.cbr.ru/hd_base/swap_info/sell/?UniDbQuery.Posted=True&UniDbQuery.From=",start,end,"&UniDbQuery.Cur=" + str(cur_in)+"&UniDbQuery.P1=0")
    value_df = gather_table("https://www.cbr.ru/hd_base/swap_info/swapinfosellvol/?UniDbQuery.Posted=True&UniDbQuery.From=",start,end,"&UniDbQuery.Cur=" + str(cur_in)+"&UniDbQuery.P1=0")

    operation_df.columns = ["Date","Date_order","Date_out","rub_rate",cur + "_rate","base_cur","swap_cbr","max_value"]
    operation_df["rub_rate"] = operation_df["rub_rate"]/100
    operation_df[cur + "_rate"] = operation_df[cur + "_rate"]/1000000
    operation_df["base_cur"] = operation_df["base_cur"]/1000000
    operation_df["swap_cbr"] =  operation_df["swap_cbr"]/1000000
    operation_df["max_value"] = operation_df["max_value"]/10

    value_df.columns = ["Date",cur +"_value_cbr","rub_value_cbr"]
    operation_df = operation_df.rename(columns = {"max_value":cur + "_max_value_cbr"})

    df_cbr_info = pd.merge(operation_df,value_df,on = "Date",how = "left").fillna(0)
    df_cbr_info["Date"] = df_cbr_info["Date"].apply(lambda x :  datetime.datetime.strptime(x,"%d.%m.%Y"))
    df_cbr_info[cur +"_value_cbr"] = df_cbr_info[cur +"_value_cbr"].apply(lambda x:float(str(x).replace(",",".").replace(" ","")))
    df_cbr_info["rub_value_cbr"] = df_cbr_info["rub_value_cbr"].apply(lambda x:float(str(x).replace(",",".").replace(" ","")))
    
    return df_cbr_info