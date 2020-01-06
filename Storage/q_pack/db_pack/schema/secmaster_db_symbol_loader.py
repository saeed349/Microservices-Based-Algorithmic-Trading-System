# -*- coding: utf-8 -*-
"""
Created on 8/31/2019

@author: Saeed Rahman
"""
from __future__ import print_function

import datetime
import psycopg2
import os


import oandapyV20
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
import configparser

import pandas as pd
import json

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.oanda_cred as oanda_cred

def parse_wiki_forex():
    """
    Download current list of OANDA Instruments.
    return:
        list of tuples to add to PostgreSQL.
    """
    now = datetime.datetime.utcnow()
    accountID=oanda_cred.acc_id_practice
    token=oanda_cred.token_practice
    client = oandapyV20.API(access_token=token)

    r = accounts.AccountInstruments(accountID=accountID)
    rv = client.request(r)

    df=pd.read_json(json.dumps(rv, indent=2))
    df=pd.io.json.json_normalize(data=df['instruments'])
    
    symbols = []
    for i, symbol in df.iterrows():
        symbols.append(
                        (symbol['name'],'Forex',
                        symbol['displayName'],
                        'Forex', 'USD', now, now)
                    )
    return symbols

def insert_new_vendor(vendor, conn):
    """
    Create a new vendor in data_vendor table.
    args:
        vendor: name of our vendor, type string.
        conn: a Postgres DB connection object
    return:
        None
    """
    todays_date = datetime.datetime.utcnow()
    cur = conn.cursor()
    cur.execute(
                "INSERT INTO data_vendor(name, created_date, last_updated_date) VALUES (%s, %s, %s)",
                (vendor, todays_date, todays_date)
                )
    conn.commit()
    

def insert_forex_symbols_postgres(symbols, conn):
    """
    Load S&P500 symbols into our PostgreSQL database.
    args:
        symbols: list of tuples which holds our stock info data.
        db_host: name of host to connect to db, type string.
        db_user: name of user_name to connect to db, type string.
        db_name: name of our database, type string.
    returns:
        None
    """

    
    column_str = """
                 ticker, instrument, name, sector, currency, created_date, last_updated_date
                 """
    insert_str = ("%s, " * 7)[:-2]
    final_str = "INSERT INTO symbol (%s) VALUES (%s)" % (column_str, insert_str)
    with conn:
        cur = conn.cursor()
        cur.executemany(final_str, symbols)

        
def load_db_info(f_name_path):
    """
    load text file holding our database credential info and the database name
    args:
        f_name_path: name of file preceded with "\\", type string
    returns:
        array of 4 values that should match text file info
    """
    cur_path = os.getcwd()
    # lets load our database credentials and info
    f = open(cur_path + f_name_path, 'r')
    lines = f.readlines()[1:]
    lines = lines[0].split(',')
    return lines


def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    
    # Connect to our PostgreSQL database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    
    symbols = parse_wiki_forex()
    insert_forex_symbols_postgres(symbols, conn)
    print("%s symbols were successfully added." % len(symbols))  
    
    vendor = 'Oanda'
    # insert new vendor to data_vendor table and fetch its id needed for stock data dump
    try:
        insert_new_vendor(vendor, conn) 
        print("Adding new Vendor ",vendor)
    except:
        print("vendor already there")
    
if __name__ == "__main__":
    main()   