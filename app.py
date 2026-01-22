import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# ============================================================
#  DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("products.csv", encoding="unicode_escape")

    # Удаляем мусорные символы
    df["State"] = df["State"].astype(str).str.replace("�", "", regex=False)
    df["State"] = df["State"].str.strip()

    # Маппинг индийских штатов → города Молдовы
    moldova_map = {
        "Andhra": "Soroca",
        "Maharashtra": "Orhei",
        "Uttar": "Chișinău",
        "Gujarat": "Ungheni",
        "Himachal": "Comrat",
        "Madhya": "Edineț",
        "Karnataka": "Bălți",
        "Delhi": "Cahul",
        "Bihar": "Hîncești",
        "Kerala": "Căușeni",
        "Punjab": "Florești",
        "Rajasthan": "Drochia",
        "Telangana": "Nisporeni",
        "Haryana": "Ștefan Vodă",
        "Jharkhand": "Leova",
        "Odisha": "Rîbnița",
        "Tamil": "Basarabeasca",
        "West": "Criuleni",
        "Assam": "Glodeni",
        "Chhattisgarh": "Cimișlia",
        "Goa": "Rezina",
        "Uttarakhand": "Ocnița",
        "Tripura": "Sângerei",
        "Nagaland": "Telenești"
    }

    def replace_to_moldova(state):
        for key, new_city in moldova_map.items():
            if key.lower() in state.lower():
                return new_city
        return state  # если это уже город Молдовы

    # Создаем колонку City
    df["City"] = df["State"].apply(replace_to_moldova)

    # Чистим Amount
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df.dropna(subset=["Amount"], inplace=True)

    # Чистим Orders
    df["Orders"] = pd.to_numeric(df["Orders"], errors="coerce")
    df["Orders"].fillna(0, inplace=True)

    return df


df = load_data()

# ============================================================
#  HEADER
# ============================================================

st.markdown(
    """
    <h1 style="text-align:center; color:white;">🔥 Полный аналитический Dashboard онлайн-магазина</h1>
    <p style="text-align:center;">Использована валюта: MDL 🇲🇩</p>
    """,
    unsafe_allow_html=True
)

# ============================================================
#  SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Фильтры")

city = st.sidebar.multiselect("Город", sorted(df["City"].unique()))
gender = st.sidebar.multiselect("Пол", sorted(df["Gender"].unique()))
age = st.sidebar.multiselect("Возрастная группа", sorted(df["Age Group"].unique()))
category = st.sidebar.multiselect("Категория товара", sorted(df["Product_Category"].unique()))

df_filtered = df.copy()

if len(city) > 0:
    df_filtered = df_filtered[df_filtered["City"].isin(city)]
if len(gender) > 0:
    df_filtered = df_filtered[df_filtered["Gender"].isin(gender)]
if len(age) > 0:
    df_filtered = df_filtered[df_filtered["Age Group"].isin(age)]
if len(category) > 0:
    df_filtered = df_filtered[df_filtered["Product_Category"].isin(category)]

# ============================================================
#  KPIs — Метрики
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Общая выручка", f"{df_filtered['Amount'].sum():,.0f} MDL")
col2.metric("🧾 Всего заказов", df_filtered["Orders"].sum())
col3.metric("🧑 Клиентов", df_filtered["User_ID"].nunique())
col4.metric("📦 Товарных категорий", df_filtered["Product_Category"].nunique())

st.markdown("---")

# ============================================================
#  SALES BY CITY
# ============================================================

st.subheader("📍 Выручка по городам")

city_rev = df_filtered.groupby("City")["Amount"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(x=city_rev.index, y=city_rev.values, palette="viridis")
plt.xticks(rotation=45)
plt.ylabel("Сумма (MDL)")
st.pyplot(fig)

# ============================================================
#  SALES BY CATEGORY
# ============================================================

st.subheader("📦 Продажи по категориям")

cat_rev = df_filtered.groupby("Product_Category")["Amount"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(x=cat_rev.index, y=cat_rev.values, palette="coolwarm")
plt.xticks(rotation=45)
plt.ylabel("Сумма (MDL)")
st.pyplot(fig)

# ============================================================
#  TOP CLIENTS TABLE
# ============================================================

st.subheader("🏆 Топ 20 клиентов по покупкам")

top_clients = (
    df_filtered.groupby(["User_ID", "Cust_name"])["Amount"]
    .sum()
    .sort_values(ascending=False)
    .head(20)
)

st.dataframe(top_clients)

# ============================================================
#  AGE-GENDER HEATMAP
# ============================================================

age_gender = (
    df_filtered.groupby(["Age Group", "Gender"])["User_ID"]
    .nunique()
    .unstack(fill_value=0)
)

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(age_gender, annot=True, fmt="d", cmap="magma")
st.pyplot(fig)


# ============================================================
#  ORDERS DISTRIBUTION
# ============================================================

st.subheader("🫧 Клиенты: заказы vs сумма покупок")

client_stats = df_filtered.groupby("User_ID").agg(
    Orders=("Orders", "sum"),
    Amount=("Amount", "sum")
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(
    client_stats["Orders"],
    client_stats["Amount"],
    s=client_stats["Amount"] / 10,
    alpha=0.6
)

ax.set_xlabel("Количество заказов")
ax.set_ylabel("Сумма покупок (MDL)")
st.pyplot(fig)

# ============================================================
#  AMOUNT DISTRIBUTION
# ============================================================

st.subheader("💸 Распределение суммы покупок")

median_amount = df_filtered["Amount"].median()

fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(df_filtered["Amount"], bins=20, kde=False)
ax.axvline(median_amount, color="red", linestyle="--", label=f"Медиана = {median_amount:.0f} MDL")

ax.set_xlabel("Сумма покупки (MDL)")
ax.set_ylabel("Количество заказов")
ax.legend()

st.pyplot(fig)



# ============================================================
# PRODUCT TABLE
# ============================================================

st.subheader("📋 Таблица товаров")

product_table = df_filtered[["Product_ID", "Product_Category", "Amount", "Orders", "City"]]
st.dataframe(product_table)

# ============================================================
# CLIENT SEARCH
# ============================================================

st.markdown("## 🔍 Поиск клиента по имени")

name = st.text_input("Введите имя клиента:")

if name:
    res = df_filtered[df_filtered["Cust_name"].str.contains(name, case=False, na=False)]
    st.dataframe(res if len(res) > 0 else "Ничего не найдено")

