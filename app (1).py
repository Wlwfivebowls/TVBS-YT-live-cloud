
import streamlit as st
import pandas as pd
import numpy as np

# 連接 Google Sheet 的 CSV 匯出連結
sheet_url = "https://docs.google.com/spreadsheets/d/1DIz9Cd5iSr1ssNkyYgvBshwKcxfkdraOYilXbXzLXhU/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(sheet_url)
    df.columns = [c.strip() for c in df.columns]
    time_col = [col for col in df.columns if '時間' in col or '時' in col][0]
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    df = df.rename(columns={time_col: '時間'})
    df = df[df['頻道名稱'].notnull()]
    return df

df = load_data()

st.title("📊 YouTube 直播頻道在線人數分析（雲端版）")
channels = df["頻道名稱"].unique().tolist()
channels.sort()

選擇模式 = st.sidebar.radio("選擇檢視模式", ["單一頻道分析", "各頻道比較"])

if 選擇模式 == "單一頻道分析":
    selected_channel = st.sidebar.selectbox("請選擇頻道", channels)
    df = df[df["頻道名稱"] == selected_channel]

min_date, max_date = df["時間"].dt.date.min(), df["時間"].dt.date.max()
start_date = st.sidebar.date_input("開始日期", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("結束日期", min_value=min_date, max_value=max_date, value=max_date)

mask = (df["時間"].dt.date >= start_date) & (df["時間"].dt.date <= end_date)
df_filtered = df[mask].copy()

df_filtered["日期"] = df_filtered["時間"].dt.date
df_filtered["小時"] = df_filtered["時間"].dt.hour

grouped = df_filtered.groupby(["頻道名稱", "日期"])
stats = grouped["在線人數"].agg(
    每日平均="mean",
    每日加總="sum",
    午間平均=lambda x: x[(x.index.hour >= 11) & (x.index.hour < 14)].mean(),
    晚間平均=lambda x: x[(x.index.hour >= 19) & (x.index.hour < 22)].mean()
).reset_index()

均值 = stats.groupby("頻道名稱")[["每日平均", "午間平均", "晚間平均"]].mean().round().sort_values("每日平均", ascending=False)
均值.index.name = "頻道名稱"
st.subheader("📈 各頻道每日平均在線人數（排序）")
st.dataframe(均值.style.highlight_max(axis=0, color="gold").set_properties(**{"font-weight": "bold", "color": "black", "background-color": "#FFD700"}))

st.subheader("📅 每日在線人數統計表")
st.dataframe(stats.round(0), use_container_width=True)

if 選擇模式 == "各頻道比較":
    import altair as alt
    hourly_avg = df_filtered.groupby(["時間", "頻道名稱"])["在線人數"].mean().reset_index()
    chart = alt.Chart(hourly_avg).mark_line().encode(
        x="時間:T", y="在線人數:Q", color="頻道名稱:N", tooltip=["時間", "頻道名稱", "在線人數"]
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)
