import datetime
import pandas as pd
import json
import time
import requests as rq
import sys

sys.path = sys.path + ['C:\\Users\\varaw\\Desktop\\Личные проекты\\Untitled Folder\\модули']

import swap
from QuikPy import QuikPy # Работа с QUIK из Python через LUA скрипты QuikSharp



def get_bid_offer (qp_provider,classcode,seccode,typ): #typ B - buy, S-sell
    if typ == "S":
        return float(qp_provider.GetQuoteLevel2(classcode, seccode)['data']["offer"][0]["price"])
    elif typ == "B":
        return float(qp_provider.GetQuoteLevel2(classcode, seccode)['data']["bid"][-1]["price"])
    
transaction_number = 1

def buy_sell(inp,typ,bs,qty = 1,price = -1): # inp в формате ["SPBFUT","GZZ4"]
    
    global transaction_number,get_bid_offer
    
    if typ == "M":
        
        if bs == "B":
            
            if (inp[0] == "SPBFUT") or (inp[0] == "FUTSPREAD"):
                
                transaction = { 
                'TRANS_ID': str(transaction_number),  # Номер транзакции задается клиентом
                'CLIENT_CODE': '',  # Код клиента. Для фьючерсов его нет
                'ACCOUNT': '-',  # Счет
                'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
                'CLASSCODE': inp[0],  # Код площадки
                'SECCODE': inp[1],  # Код тикера
                'OPERATION': bs,  # B = покупка, S = продажа
                'PRICE': str(int(get_bid_offer(*inp,bs)*1.05)),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
                'QUANTITY': str(qty),  # Кол-во в лотах
                'TYPE': typ}  # L = лимитная заявка (по умолчанию), M = рыночная заявка
                
                print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}',transaction_number)
                transaction_number += 1
            else:
                
                transaction = { 
                'TRANS_ID': str(transaction_number),  # Номер транзакции задается клиентом
                'CLIENT_CODE': '-',  # Код клиента. Для фьючерсов его нет
                'ACCOUNT': '-',  # Счет
                'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
                'CLASSCODE': inp[0],  # Код площадки
                'SECCODE': inp[1],  # Код тикера
                'OPERATION': bs,  # B = покупка, S = продажа
                'PRICE': str(0),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
                'QUANTITY': str(qty),  # Кол-во в лотах
                'TYPE': typ}  # L = лимитная заявка (по умолчанию), M = рыночная заявка

                print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}',transaction_number)
                transaction_number += 1
        else:
            
            if (inp[0] == "SPBFUT") or (inp[0] == "FUTSPREAD"):
                
                transaction = { 
                'TRANS_ID': str(transaction_number),  # Номер транзакции задается клиентом
                'CLIENT_CODE': '',  # Код клиента. Для фьючерсов его нет
                'ACCOUNT': '-',  # Счет
                'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
                'CLASSCODE': inp[0],  # Код площадки
                'SECCODE': inp[1],  # Код тикера
                'OPERATION': bs,  # B = покупка, S = продажа
                'PRICE': str(int(get_bid_offer(*inp,bs)*0.95)),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
                'QUANTITY': str(qty),  # Кол-во в лотах
                'TYPE': typ}  # L = лимитная заявка (по умолчанию), M = рыночная заявка
                
                print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}',transaction_number)
                transaction_number += 1
            else:
                
                transaction = { 
                'TRANS_ID': str(transaction_number),  # Номер транзакции задается клиентом
                'CLIENT_CODE': '-',  # Код клиента. Для фьючерсов его нет
                'ACCOUNT': '-',  # Счет
                'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
                'CLASSCODE': inp[0],  # Код площадки
                'SECCODE': inp[1],  # Код тикера
                'OPERATION': bs,  # B = покупка, S = продажа
                'PRICE': str(0),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
                'QUANTITY': str(qty),  # Кол-во в лотах
                'TYPE': typ}  # L = лимитная заявка (по умолчанию), M = рыночная заявка

                print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}',transaction_number)
                transaction_number += 1