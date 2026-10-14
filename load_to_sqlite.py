"""Загружает датасет Telco Customer Churn в локальную базу SQLite (telco.db).
После запуска можно открывать telco.db в DB Browser for SQLite или DBeaver
и выполнять запросы из queries.sql.
"""
import sqlite3

import pandas as pd

URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)

df = pd.read_csv(URL)
# У 11 новых клиентов (tenure = 0) TotalCharges пустой: заполняем нулём
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)

with sqlite3.connect("telco.db") as con:
    df.to_sql("customers", con, if_exists="replace", index=False)
    print("Загружено строк:", con.execute("SELECT COUNT(*) FROM customers").fetchone()[0])
