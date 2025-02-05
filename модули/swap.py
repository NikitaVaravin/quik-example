import pandas as pd
import requests as rq
import json
import datetime
import numpy as np

import iss
import model_func as mf
import cbr_parcer as cb_ps

def kontango_rate(cur_par,start,end,lot,link,regime):
    
    def make_rate_swap (term,ruonia,price,swap):
        return (1/term)*(((ruonia*term+365)*price)/(swap+price) - 365)

    df_fut = iss.get_cand(["futures","forts","RFUD"],cur_par[0],1,start,end)
    df_tom = iss.get_cand(["currency","selt","CETS"],cur_par[1],1,start,end)

    df_fut = df_fut.loc[:,["close","end"]].rename(columns = {"close":"price_fut"}).assign(exp_date = iss.get_exp_date(cur_par[0]))
    df_fut["price_fut"] = df_fut["price_fut"].apply(lambda x:x/lot)
    df_tom = df_tom.loc[:,["close","end"]].rename(columns = {"close":"price_spot"})
   
    df = pd.merge(df_fut,df_tom,on = "end")
    
    if regime != "direct":
        df["price_fut"] = df["price_fut"].apply(lambda x:1/x)
        df["price_spot"] = df["price_spot"].apply(lambda x:1/x)

    df["exp_date"] = df["exp_date"].apply(lambda x:datetime.datetime.strptime(str(pd.to_datetime(x).date()),"%Y-%m-%d"))
    df["end"] = df["end"].apply(lambda x:datetime.datetime.strptime(str(pd.to_datetime(x).date()),"%Y-%m-%d"))

    df = df.assign(TERM = (df["exp_date"] - df["end"]))
    df["TERM"] = df["TERM"].apply(lambda x:x.days + 1)


    df = df.rename(columns = {"end":"Date"})
    
    if link == "cbr":
        ruonia = cb_ps.gather_ruonia(start,end)
    else:
        ruonia = pd.read_excel(link)

    df = pd.merge(df,ruonia,on = "Date")

    df = df.assign(kontango = df["price_fut"] - df["price_spot"])
    df = df.assign(kontango_rate = make_rate_swap(df["TERM"],df["ruonia"],df["price_spot"],df["kontango"]))
    
    df_end = df.groupby(["Date"]).agg({"kontango_rate":"mean","price_fut":"mean"}).reset_index()
    df_end = df_end.rename(columns = {"kontango_rate":"kontango_rate_"+cur_par[1][:3],"price_fut":"price_fut_"+cur_par[1][:3]})
                           
    return df_end

def kontango_make(list_of_fut,start,cur,lot,link = "cbr",regime = "direct"):
    df_swap = pd.DataFrame()
    params = [lot,link,regime]
    temp_list = []
    
    for i in list_of_fut:
        if len(df_swap) == 0:
            df_swap = kontango_rate([i,cur],str(start.date()),str((start+datetime.timedelta(days = 90)).date()),*params).iloc[:-2]
            start = df_swap.iloc[-1][0].date()
            print(start)

        elif i == list_of_fut[-1]:
            df_swap = pd.concat([df_swap,kontango_rate([i,cur],str(start),str((start+datetime.timedelta(days = 90))),*params).iloc[1:]])
                                
                              
        else:
            df_swap = pd.concat([df_swap,kontango_rate([i,cur],str(start),str((start+datetime.timedelta(days = 90))),*params).iloc[1:-2]])
            start = df_swap.iloc[-1][0].date()
            print(start)
        
    return df_swap