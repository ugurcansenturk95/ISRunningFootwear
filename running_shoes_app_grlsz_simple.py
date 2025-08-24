
import streamlit as st
import pandas as pd
from pathlib import Path
from helpers_grlsz import build_normalized_view, resolve_output_columns, apply_filters, load_df

st.set_page_config(page_title="Intersport Running Footwear — Simple", layout="wide")
st.title("Intersport Running Footwear")

with st.sidebar:
    st.caption("Veri yükleyin ya da aynı klasöre 'Kod _n_ son grlsz.xlsx' koyun.")

df_raw, source_label = load_df()
st.caption(f"Kaynak: {source_label}")

dfn = build_normalized_view(df_raw)
out_cols = resolve_output_columns(df_raw)

col1, col2 = st.columns(2)
with col1:
    q1 = st.radio("1) Cinsiyet", ["Erkek", "Kadin"], horizontal=True, index=0)
    q3 = st.radio("3) Hedef", ["Yaris", "Antrenman"], horizontal=True, index=0)
    q5 = st.radio("5) Mesafe (her koşu)", ["0-20 km", "20 km ve daha fazla"], horizontal=True, index=0)
    q7 = st.radio("7) Pronasyon (İçe Basma)", ["Evet", "Hayir"], horizontal=True, index=1)
with col2:
    q2 = st.radio("2) Zemin", ["Road", "Trail"], horizontal=True, index=0)
    q4 = st.radio("4) Haftalık sıklık", ["3 ve daha az", "4 ve daha fazla"], horizontal=True, index=0)
    q6 = st.radio("6) Diz/Kalça sakatlığı", ["Var", "Yok"], horizontal=True, index=1)

params = dict(gender=q1, surface=q2, goal=q3, freq=q4, distance=q5, injury=q6, pronation=q7)
filtered = apply_filters(dfn, params)
show_cols = [c for c in out_cols if c in filtered.columns]

st.subheader("Öneriler")
st.caption(f"Toplam sonuç: {len(filtered)}")
if len(filtered) == 0:
    st.warning("Gösterilecek sonuç yok. Seçimleri değiştirip tekrar deneyin.")
else:
    st.dataframe(filtered[show_cols], use_container_width=True)
    csv = filtered[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button("CSV indir", data=csv, file_name="intersport_running_footwear.csv", mime="text/csv")
