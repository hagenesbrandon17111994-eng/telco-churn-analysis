-- Проект 1. Анализ оттока клиентов (Telco Customer Churn)
-- Таблица: customers (одна строка = один клиент), Churn = 'Yes' / 'No'
-- Синтаксис совместим с SQLite и PostgreSQL.

-- Q1. Общий churn rate и доля выручки, которую «унесли» ушедшие клиенты
SELECT
    COUNT(*)                                                        AS clients,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)                  AS churned,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 1) AS churn_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END)
                / SUM(MonthlyCharges), 1)                           AS churned_revenue_share_pct
FROM customers;

-- Q2. Churn по типу договора (GROUP BY + CASE)
SELECT
    Contract,
    COUNT(*)                                                        AS clients,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2)                                   AS avg_monthly_charge
FROM customers
GROUP BY Contract
ORDER BY churn_rate_pct DESC;

-- Q3. Churn по стажу клиента (бакеты через CASE)
SELECT
    CASE
        WHEN tenure <= 12 THEN '1) 0-12 мес'
        WHEN tenure <= 24 THEN '2) 13-24 мес'
        WHEN tenure <= 48 THEN '3) 25-48 мес'
        ELSE                   '4) 49-72 мес'
    END                                                             AS tenure_bucket,
    COUNT(*)                                                        AS clients,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 1) AS churn_rate_pct
FROM customers
GROUP BY 1
ORDER BY 1;

-- Q4. Рейтинг сегментов «договор x способ оплаты» (CTE + оконные функции)
-- Показывает, какой вклад каждый сегмент вносит в общий отток.
WITH segments AS (
    SELECT
        Contract,
        PaymentMethod,
        COUNT(*)                                            AS clients,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned
    FROM customers
    GROUP BY Contract, PaymentMethod
)
SELECT
    Contract,
    PaymentMethod,
    clients,
    churned,
    ROUND(100.0 * churned / clients, 1)                     AS churn_rate_pct,
    ROUND(100.0 * churned / SUM(churned) OVER (), 1)        AS share_of_all_churn_pct,
    RANK() OVER (ORDER BY 1.0 * churned / clients DESC)     AS risk_rank
FROM segments
ORDER BY risk_rank;

-- Q5. Накопительный вклад сегментов в отток (оконная сумма, принцип Парето)
WITH seg AS (
    SELECT
        Contract || ' / ' || PaymentMethod                  AS segment,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)      AS churned
    FROM customers
    GROUP BY Contract, PaymentMethod
)
SELECT
    segment,
    churned,
    ROUND(100.0 * churned / SUM(churned) OVER (), 1)        AS share_pct,
    ROUND(100.0 * SUM(churned) OVER (ORDER BY churned DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                / SUM(churned) OVER (), 1)                  AS cumulative_share_pct
FROM seg
ORDER BY churned DESC;

-- Q6. Влияние дополнительных услуг на churn: сколько услуг подключено у клиента
-- (только клиенты с интернетом)
WITH services AS (
    SELECT
        customerID,
        Churn,
        (OnlineSecurity = 'Yes') + (OnlineBackup = 'Yes') + (DeviceProtection = 'Yes')
          + (TechSupport = 'Yes') + (StreamingTV = 'Yes') + (StreamingMovies = 'Yes')
                                                            AS n_services
    FROM customers
    WHERE InternetService <> 'No'
)
SELECT
    n_services,
    COUNT(*)                                                AS clients,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 1) AS churn_rate_pct
FROM services
GROUP BY n_services
ORDER BY n_services;

-- Q7. Внутри каждого типа договора: какие клиенты платят больше среднего
-- и как у них с оттоком (оконное среднее по партиции)
WITH base AS (
    SELECT
        Contract,
        Churn,
        MonthlyCharges,
        AVG(MonthlyCharges) OVER (PARTITION BY Contract)    AS avg_in_contract
    FROM customers
)
SELECT
    Contract,
    CASE WHEN MonthlyCharges > avg_in_contract THEN 'выше среднего по договору'
         ELSE 'ниже среднего по договору' END               AS price_level,
    COUNT(*)                                                AS clients,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 1) AS churn_rate_pct
FROM base
GROUP BY Contract, price_level
ORDER BY Contract, price_level;

-- Q8. Оценка эффекта: сколько клиентов и выручки в месяц сохраним, если в сегменте
-- «помесячный договор + электронный чек» снизить churn на 10 п.п. (сценарий)
WITH hot AS (
    SELECT
        COUNT(*)                                            AS clients,
        AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END)    AS churn_rate,
        AVG(MonthlyCharges)                                 AS avg_charge
    FROM customers
    WHERE Contract = 'Month-to-month' AND PaymentMethod = 'Electronic check'
)
SELECT
    clients,
    ROUND(100 * churn_rate, 1)                              AS current_churn_pct,
    ROUND(clients * 0.10)                                   AS clients_saved,
    ROUND(clients * 0.10 * avg_charge)                      AS monthly_revenue_saved
FROM hot;
