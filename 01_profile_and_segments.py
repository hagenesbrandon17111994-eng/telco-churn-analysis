"""Проект 1. Анализ оттока клиентов (Telco Customer Churn).
Шаг 1: загрузка, чистка, общий churn rate, первая сегментация.

Данные: https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
Запуск: python 01_profile_and_segments.py
"""
import pandas as pd

URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)

# ---------- 1. Загрузка ----------
df = pd.read_csv(URL)
print("Размер:", df.shape)
print("Дубликатов customerID:", df.customerID.duplicated().sum())

# ---------- 2. Чистка ----------
# TotalCharges читается как текст: у 11 клиентов с tenure = 0 значение пустое.
# Это новые клиенты, ещё ничего не оплатившие, поэтому заполняем нулём.
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
df["churn"] = (df["Churn"] == "Yes").astype(int)
df["tenure_bucket"] = pd.cut(
    df["tenure"], [-1, 12, 24, 48, 72], labels=["0-12", "13-24", "25-48", "49-72"]
)

# ---------- 3. Общий churn rate ----------
print(f"\nChurn rate: {df.churn.mean():.1%}")
lost = df.loc[df.churn == 1, "MonthlyCharges"].sum()
print(f"Доля месячной выручки, ушедшей с оттоком: {lost / df.MonthlyCharges.sum():.1%}")


# ---------- 4. Сегментация ----------
def churn_by(col: str) -> pd.DataFrame:
    g = df.groupby(col, observed=True).agg(
        clients=("churn", "size"), churn_rate=("churn", "mean")
    )
    g["churn_rate"] = (g["churn_rate"] * 100).round(1)
    return g


for col in [
    "Contract",
    "PaymentMethod",
    "InternetService",
    "tenure_bucket",
    "TechSupport",
    "PaperlessBilling",
    "SeniorCitizen",
]:
    print(f"\n--- {col} ---")
    print(churn_by(col))

# ---------- 5. Самый «горячий» сегмент ----------
hot = df[(df.Contract == "Month-to-month") & (df.PaymentMethod == "Electronic check")]
print(
    f"\nПомесячный договор + электронный чек: {len(hot)} клиентов, "
    f"churn {hot.churn.mean():.1%}, "
    f"{hot.churn.sum() / df.churn.sum():.1%} всех ушедших"
)
