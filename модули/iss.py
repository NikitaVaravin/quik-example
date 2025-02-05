import requests as rq
import json
import numpy as np
from selenium import webdriver
import pandas as pd
from scipy import optimize
import datetime
from nelson_siegel_svensson.calibrate import calibrate_nss_ols

def get_bond (isin,regime_search = -1): # get_ofz("SU26222RMFS8") 
# функция получения информации об облигации, купоны их даты выплаты и оферта
# на вход подается isin облигации, на выходе выдается список из датафрейма всех будущих выплат и датой оферты

    r = rq.get("https://iss.moex.com/iss/securities/" + isin + "/bondization.json?iss.json=extended&iss.meta=off&lang=ru&limit=unlimited")

    nominal_df = pd.json_normalize(json.loads(r.content)[1]["amortizations"])
    offers = pd.json_normalize(json.loads(r.content)[1]["offers"])

    nominal_df = nominal_df.loc[:,["isin","amortdate","value","value_rub","faceunit"]]
    nominal_df["amortdate"] = nominal_df["amortdate"].apply(lambda x:datetime.datetime.strptime(str(x),"%Y-%m-%d"))
    nominal_df = nominal_df.rename(columns = {"amortdate":"coupondate"})

    coupon_df = pd.DataFrame()
    for i in range(len(json.loads(r.content)[1]["coupons"])):

        temp_df = pd.DataFrame.from_dict(json.loads(r.content)[1]["coupons"][i],orient = "index").T

        if i == 0:
            coupon_df = temp_df

        else:
            coupon_df = pd.concat([coupon_df,temp_df],ignore_index=True)

    coupon_df = coupon_df.loc[:,["isin","coupondate","value","value_rub","faceunit"]]
    coupon_df["coupondate"] = coupon_df["coupondate"].apply(lambda x:datetime.datetime.strptime(str(x),"%Y-%m-%d"))

    ofz_df = pd.concat([coupon_df,nominal_df],ignore_index=True)
    if regime_search != "all":
        ofz_df = ofz_df[ofz_df["coupondate"] > datetime.datetime.today()]

    year_rows = ofz_df["coupondate"] - datetime.datetime.today()
    year_rows = year_rows.apply(lambda x : x.days/365)
    ofz_df = ofz_df.assign(years = year_rows)

    return [ofz_df,offers]

def get_YTM(df,price,nkd): 
    def make_opt (vec,vec_coup,price):
        return lambda x : np.sum(vec_coup/(x+1)**vec) - price
    
    return optimize.newton(make_opt(df["years"],df["value_rub"],price + nkd), 0.1)

def get_price_nkd (isin,boards):
    r = rq.get("https://iss.moex.com/iss/engines/stock/markets/bonds/boards/"+ boards +"/securities/"+ isin +".jsonp?iss.meta=off&iss.only=securities%2Cmarketdata%2Cmarketdata_yields&lang=ru")
    process = r.content  
    #[price,nominal,nkd,ISSUESIZE]
    return [json.loads(process)['marketdata']["data"][0][27],json.loads(process)['securities']["data"][0][38], #цена работает плохо
            json.loads(process)["securities"]["data"][0][7],
           json.loads(process)["securities"]["data"][0][16]] 

def make_price(df,nss):
    vec_interest = nss(df["years"])
    vec_interest = (vec_interest+1)**df["years"]
    
    price  = np.sum(df["value_rub"]/vec_interest)
    
    return price

def make_nkd(df):
    return round(df.iloc[0][2]*(0.5 - df.iloc[0][3])*2,2)

def get_current_ytm_table(isin_lists):
    
    ytm_current_df = pd.DataFrame(columns = ["isin","ytm","years"])

    for i in isin_lists:
        temp_ofz_df = get_bond(i)[0]
        row = pd.DataFrame(data = [[i,get_YTM(get_bond(i)[0],*get_price_nkd(i,"TQOB")),np.max(temp_ofz_df["years"])]], columns =   ["isin","ytm","years"])

        ytm_current_df = pd.concat([ytm_current_df,row],ignore_index=True)
        
    return ytm_current_df

def make_current_nss(isin_lists):

    global get_current_ytm_table
    
    process_df = get_current_ytm_table(isin_lists)
    
    t = process_df["years"].to_numpy()
    y = process_df["ytm"].to_numpy()
    
    nss, status = calibrate_nss_ols(t, y, tau0 = (2,5))
    
    return nss

def get_z_spread(isin,boards,current_nss):
    
    global get_bond,get_price_nkd
    
    df = get_bond(isin)[0]
    price,nkd = get_price_nkd(isin,boards)
    df = df.assign(spot_curve = current_nss(df["years"]))
    
    def make_opt (vec,vec_coup,g_vec,price):
        return lambda z : np.sum(vec_coup/(g_vec + z + 1)**vec) - price
    
    return optimize.newton(make_opt(df["years"],df["value_rub"],df["spot_curve"],price + nkd),0.01)

def make_body_price (df,ytm):
    return np.sum(df["value_rub"]/((1+ytm)**df["years"]))

def duration(isin,ytm = -1):
    global get_bond,get_price_nkd,get_YTM,make_body_price
    
    ofz = get_bond(isin)[0]
    ofz_price_nkd = get_price_nkd(isin)
    if ytm == -1:
        ofz_ytm = get_YTM(ofz,*ofz_price_nkd)
    else:
        ofz_ytm = ytm
        ofz_price_nkd = [make_body_price(ofz,ofz_ytm),ofz_price_nkd[1]]
        
    
    
    x = 0.0001
    duration_plus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm + x))/x/ofz_price_nkd[0]
    duration_minus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm - x))/x/ofz_price_nkd[0]
    
    x_2 = 0.001
    
    delta_2_plus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm + x_2))/ofz_price_nkd[0]
    delta_2_minus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm - x_2))/ofz_price_nkd[0]
    
    duration_2_plus = (delta_2_plus - duration_plus*x_2)/(x_2**2)
    duration_2_minus = (delta_2_minus - duration_minus*x_2)/(x_2**2)
    
#    x_3 = 0.01
#    
#    delta_3_plus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm + x_3))/ofz_price_nkd[0]
#    delta_3_minus = (make_body_price(ofz,ofz_ytm) - make_body_price(ofz,ofz_ytm - x_3))/ofz_price_nkd[0]
#    
#    duration_3_plus = (delta_3_plus - duration_plus*x_3 - duration_2_plus*(x_3**2))/(x_3**3)
#    duration_3_minus = (delta_3_minus - duration_minus*x_3 - duration_2_minus*(x_3**2))/(x_3**3)
    
    return [-1*(duration_plus - duration_minus)/2,-1*(duration_2_plus + duration_2_minus)/2]

#добавить реинвестирование
def make_sdvig (isin,nss,time):
    
    global get_bond,make_price,get_price_nkd,make_nkd
    
    ofz_df = get_bond(isin)[0]
    price_nkd = get_price_nkd(isin)
    ofz_df["years"] = ofz_df["years"] - time
    
    coupon_payments = np.sum(ofz_df[ofz_df["years"] < 0]["value_rub"])
    ofz_df_new = ofz_df[ofz_df["years"] >=0]
    
    if ofz_df_new.shape[0] == 0:
        return [0,0,coupon_payments]
    else:
        new_price = make_price(ofz_df_new,nss)

        return [new_price,make_nkd(ofz_df_new),coupon_payments]

#получить свечи    
def get_cand(boards,isin,interval,start,end):
    
    def get_rqst(boards_in,isin_in,interval_in,start_in,end_in):
        
        r = rq.get("https://iss.moex.com/iss/engines/" + boards_in[0] +"/markets/" + boards_in[1] +"/boards/"+ boards_in[2]
           + "/securities/" + isin_in
           + "/candles.json?from=" + start_in
           + "&till=" + end_in
           + "&interval=" + str(interval_in))
        
        return pd.DataFrame(json.loads(r.content)["candles"]["data"],columns = json.loads(r.content)["candles"]["columns"])
    
    start = datetime.datetime.strptime(start,"%Y-%m-%d")
    end = datetime.datetime.strptime(end,"%Y-%m-%d")
    
    delta = (end - start).days
    
    if interval < 5:
    
        iteration = delta//1
        tail = delta%1
        
    else:
        
        iteration = delta//30
        tail = delta%30
        
    df = get_rqst(boards,isin,interval,
    str(end - datetime.timedelta(days = tail))[:-9],
    str(end)[:-9])
    
    for i in range(iteration):
        
        if interval < 5:
                        
            df = pd.concat([df,get_rqst(boards,isin,interval,
                str(start + datetime.timedelta(days =1)*i)[:-9],
                str(start + datetime.timedelta(days =1)*(i+1))[:-9])])
            
        else:
            
            df = pd.concat([df,get_rqst(boards,isin,interval,
                str(start + datetime.timedelta(days =30)*i)[:-9],
                str(start + datetime.timedelta(days =30)*(i+1))[:-9])])
    
    df["begin"] = df["begin"].apply(lambda x : pd.Timestamp(x))
    df["end"] = df["end"].apply(lambda x : pd.Timestamp(x))
    
    df = df.sort_values(by = ["begin"])
    
    return df.reset_index(drop = True)


def get_exp_date(isin_in):
    
    if int(isin_in[-1]) < 4:
        
        r = rq.get("https://iss.moex.com/iss/statistics/engines/futures/markets/forts/securities/" + isin_in + "/outdated.jsonp?iss.meta=off")
        
        return pd.DataFrame(json.loads(r.content)["securities"]["data"],columns = json.loads(r.content)["securities"]["columns"])["IMTIME"][0]
        
    else:
        
        r = rq.get("https://iss.moex.com/iss/engines/futures/markets/forts/boards/RFUD/securities/"+ isin_in +".jsonp?iss.meta=off")

        return pd.DataFrame(json.loads(r.content)["securities"]["data"],columns = json.loads(r.content)["securities"]["columns"])["LASTTRADEDATE"][0]