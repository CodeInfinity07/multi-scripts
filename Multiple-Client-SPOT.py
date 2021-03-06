#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 26 10:05:16 2021

@author: ryzon
"""
import asyncio
import os
import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance import ThreadedWebsocketManager
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import re
import mysql.connector
import logging
import ray

ray.init()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater('2028793873:AAFAHKocwFb8aFA5aGVRIAgnL0Tm2ycHhGc', use_context=True)
try:
    connection = mysql.connector.connect(host='166.62.25.253',
                                         database='binance-db',
                                         user='mitesh_jb',
                                         password='MITESHmitesh@2')
except Exception as e:
    print(e)

def nospecial(text):
	text = re.sub("[^a-zA-Z0-9]+", " ",text)
	return text

def extract_perc(perc, num):
    result = float((perc/100)*num)
    return float(result)

def get_account_balances():
    balance = client.get_account()
    return balance

def get_account_balance(asset):
    balance = client.get_asset_balance(asset=asset,timestamp=client.get_server_time()['serverTime'])
    return balance['free']


def buy_symbol(symbol, quantity, price):
    try:
        buy_market = client.create_order(
            symbol=symbol,
            side='BUY',
            type='LIMIT',
            quantity=quantity,
            timeInForce='GTC',
            price=price,
            timestamp=client.get_server_time()['serverTime'],
            newOrderRespType='FULL')

        return buy_market

    except BinanceAPIException as e:
        return e
    except BinanceOrderException as e:
        return e

def sell_oco_symbol(symbol, quantity, r, t_price , t_limit_price):
    try:
        sell_market = client.order_oco_sell(
            symbol= symbol,
            quantity= quantity,
            price= r,
            stopPrice= t_price,
            stopLimitPrice= t_limit_price,
            stopLimitTimeInForce= 'GTC',
            timestamp=client.get_server_time()['serverTime'])

        return sell_market

    except BinanceAPIException as e:
        return e
    except BinanceOrderException as e:
        return e

def parser(update, context):
    global client
    try:
        temp = update.message.text
    except:
        temp = update.channel_post.text
    target = temp.lower()
    sql_select_Query = "select * from clients"
    cursor = connection.cursor()
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    for row in records:
        testnet_api_key = str(row[7])
        testnet_secret_key = str(row[8])
        client = Client(testnet_api_key, testnet_secret_key)
        client.API_URL = 'https://testnet.binance.vision/api'
        BUY_PERCENT = float(row[9])
        SELL_PERCENT = float(row[10])
        ST_PRICE_PERCENT = float(row[11])
        STL_PRICE_PERCENT = float(row[12])
        DEFAULT_USDT = float(row[13])
        hatcher.remote(target, BUY_PERCENT,SELL_PERCENT,ST_PRICE_PERCENT,STL_PRICE_PERCENT,DEFAULT_USDT)
    
@ray.remote
def hatcher(target,BUY_PERCENT,SELL_PERCENT,ST_PRICE_PERCENT,STL_PRICE_PERCENT,DEFAULT_USDT):
    if "zone" in target:
        pass
    elif "short" in target:
        pass
    elif "buy" in target:
        try:
            index_hash = target.lower().index('#')
            token = nospecial(target[index_hash+1:])
        except:
            index_hash = 0
            token = nospecial(target[index_hash])
        if "rebuy" in token.lower():
            index_reb = token.lower().index('rebuy')
            token = token[:index_reb]
        if "buy" in token.lower():
            index_reb = token.lower().index('buy')
            token = token[:index_reb]
        if "spot" in token.lower():
            index_reb = token.lower().index('spot')
            token = token[:index_reb]
        if "setup" in token.lower():
            index_reb = token.lower().index('setup')
            token = token[:index_reb]
        if "scalp" in token.lower():
            index_reb = token.lower().index('scalp')
            token = token[:index_reb]
        token = str(token)+'USDT'
        token = token.replace(" ",'')
        token = token.upper()
        try:
            exchange_info = client.get_orderbook_ticker(symbol=token)
            div_value = float(exchange_info['askPrice'])
            value = float(div_value) + extract_perc(BUY_PERCENT, div_value)
            price_precision = str(float(div_value))
            prc_precision_index = price_precision.index('.')
            prc_precision = len(price_precision) - prc_precision_index - 1
            if int(prc_precision) == 1 and int(price_precision[-1])==0:
                prc_zero_precision=True
            else:
                prc_zero_precision = False
            quantity_precision = float(exchange_info['askQty'])
            quantity_precision = str(float(quantity_precision))
            qty_precision_index = quantity_precision.index('.')
            qty_precision = len(quantity_precision) - qty_precision_index - 1
            if int(qty_precision) == 1 and int(quantity_precision[-1])==0:
                qty_zero_precision=True
            else:
                qty_zero_precision = False
            qs = float(DEFAULT_USDT/value)
            qs = round(qs, qty_precision)
            price = round(value, prc_precision)
            try:
                resp = buy_symbol(token, qs, price)
                print(resp)
                avg_value = 0
                items = 0
                for key,value in resp.items():
                    if 'price' == key:
                        avg_value = float(avg_value) + float(value)
                        items = float(items) + float(1)
                temp_price = float(avg_value/items)
                total_price = float(temp_price) - extract_perc(ST_PRICE_PERCENT, temp_price)
                t_price = round(total_price, prc_precision)
                total_limit_price = float(temp_price) - extract_perc(STL_PRICE_PERCENT, temp_price)
                t_limit_price = round(total_limit_price, prc_precision)
                total_pr = temp_price + extract_perc(SELL_PERCENT, temp_price)
                r = round(total_pr, prc_precision)
                if prc_zero_precision == True and qty_zero_precision == True:
                    resp2 = sell_oco_symbol(token, int(qs) ,int(r) , int(t_price), int(t_limit_price))
                elif prc_zero_precision == False and qty_zero_precision == True:
                    resp2 = sell_oco_symbol(token, int(qs) ,r , t_price, t_limit_price)
                elif prc_zero_precision == True and qty_zero_precision == False:
                    resp2 = sell_oco_symbol(token, qs ,int(r) , int(t_price), int(t_limit_price))
                else:
                    resp2 = sell_oco_symbol(token, qs ,r , t_price, t_limit_price)
                print(resp2)
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
                
updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), parser))
updater.start_polling(timeout=30)
updater.idle()
