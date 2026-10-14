"""Проект 1. Анализ оттока клиентов (Telco Customer Churn).
Шаг 3: графики для README. Запуск: python 02_charts.py
Результат: папка charts/ с четырьмя PNG.
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)
SOURCE = "Источник: Telco Customer Churn (IBM), 7043 клиента"

# Палитра: один акцент, остальное серое
BG, PRIMARY, WHITE = "#e8f2ff", "#222222", "#FFFFFF"
ACCENT, MUTED_BAR, MUTED_TXT = "#006dca", "#b8b8b8", "#6f6f6f"

plt.rcParams["font.family"] = "DejaVu Sans"
OUT = Path("charts")
OUT.mkdir(exist_ok=True)

# ---------- Данные ----------
df = pd.read_csv(URL)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
df["churn"] = (df["Churn"] == "Yes").astype(int)


def rate(col):
    return (df.groupby(col, observed=True)["churn"].mean() * 100).round(1)


def base_axes(title, subtitle, w=8, h=4.6):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    fig.text(0.05, 0.96, textwrap.fill(title, 58), fontsize=13, fontweight="bold",
             color=PRIMARY, va="top", linespacing=1.25)
    fig.text(0.05, 0.80, textwrap.fill(subtitle, 85), fontsize=9.5, color=PRIMARY, va="top")
    ax = fig.add_axes([0.07, 0.14, 0.88, 0.54])
    ax.set_facecolor(BG)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=10, colors=PRIMARY)
    fig.text(0.05, 0.03, SOURCE, fontsize=7, color=MUTED_TXT, style="italic")
    return fig, ax


def bar_chart(fname, title, subtitle, labels, values, highlight):
    fig, ax = base_axes(title, subtitle)
    colors = [ACCENT if i in highlight else MUTED_BAR for i in range(len(values))]
    bars = ax.bar(labels, values, color=colors, width=0.6, zorder=3)
    ax.grid(axis="y", color=WHITE, lw=1.0, zorder=1)
    ax.set_ylim(0, max(values) * 1.18)
    ax.set_yticks([])
    ax.grid(False)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + max(values) * 0.02, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color=PRIMARY)
    fig.savefig(OUT / fname, dpi=200, facecolor=BG)
    plt.close(fig)


# ---------- 1. Договор ----------
c = rate("Contract").reindex(["Month-to-month", "One year", "Two year"])
bar_chart(
    "1_churn_by_contract.png",
    "Клиенты с помесячным договором уходят в 15 раз чаще, чем с двухлетним",
    "Доля ушедших клиентов по типу договора, %",
    ["Помесячный", "Годовой", "Двухлетний"], c.values, highlight=[0],
)

# ---------- 2. Стаж ----------
df["tenure_bucket"] = pd.cut(df.tenure, [-1, 12, 24, 48, 72],
                             labels=["0-12 мес.", "13-24 мес.", "25-48 мес.", "49-72 мес."])
t = rate("tenure_bucket")
bar_chart(
    "2_churn_by_tenure.png",
    "Почти половина новых клиентов уходит в первый год",
    "Доля ушедших клиентов по сроку жизни, %",
    list(t.index), t.values, highlight=[0],
)

# ---------- 3. Число услуг ----------
inet = df[df.InternetService != "No"].copy()
svc = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
       "StreamingTV", "StreamingMovies"]
inet["n_services"] = (inet[svc] == "Yes").sum(axis=1)
s = (inet.groupby("n_services")["churn"].mean() * 100).round(1)
bar_chart(
    "3_churn_by_services.png",
    "Каждая подключённая услуга снижает отток: при шести он почти нулевой",
    "Доля ушедших клиентов по числу доп. услуг, % (только клиенты с интернетом)",
    [str(i) for i in s.index], s.values, highlight=[0],
)

# ---------- 4. Парето по сегментам ----------
seg = (df.groupby(["Contract", "PaymentMethod"])["churn"].sum()
         .sort_values(ascending=False))
share = (seg / seg.sum() * 100).round(1)
names_ru = {"Month-to-month": "Помесячный", "One year": "Годовой", "Two year": "Двухлетний",
            "Electronic check": "эл. чек", "Mailed check": "бумажный чек",
            "Bank transfer (automatic)": "автоплатёж (банк)",
            "Credit card (automatic)": "автоплатёж (карта)"}
labels = [f"{names_ru[a]} + {names_ru[b]}" for a, b in share.index][:6]
vals = share.values[:6]
cum4 = share.values[:4].sum()

fig, ax = base_axes(
    f"Четыре сегмента с помесячным договором дают {cum4:.0f}% всего оттока",
    "Доля сегмента в общем числе ушедших клиентов, % (шесть крупнейших сегментов)",
    h=4.8,
)
ax.set_position([0.36, 0.14, 0.58, 0.54])
y = list(range(len(vals)))[::-1]
colors = [ACCENT if i < 4 else MUTED_BAR for i in range(len(vals))]
ax.barh(y, vals, color=colors, height=0.6, zorder=3)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xticks([])
ax.set_xlim(0, max(vals) * 1.15)
for yi, v in zip(y, vals):
    ax.text(v + 0.8, yi, f"{v:.1f}%", va="center", fontsize=10, fontweight="bold", color=PRIMARY)
fig.savefig(OUT / "4_churn_pareto_segments.png", dpi=200, facecolor=BG)
plt.close(fig)

print("Готово:", *sorted(p.name for p in OUT.glob("*.png")), sep="\n  ")
