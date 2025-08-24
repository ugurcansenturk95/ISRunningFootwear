
import streamlit as st
from pathlib import Path
from helpers_grlsz import build_normalized_view, resolve_output_columns, apply_filters, load_df

st.set_page_config(page_title="Intersport Running Footwear — Wizard", layout="centered")
st.title("Intersport Running Footwear")

with st.sidebar:
    st.caption("Veri yükleyin ya da aynı klasöre 'Kod _n_ son grlsz.xlsx' koyun.")

df_raw, source_label = load_df()
st.caption(f"Kaynak: {source_label}")

dfn = build_normalized_view(df_raw)
out_cols = resolve_output_columns(df_raw)

if "step" not in st.session_state:
    st.session_state.step = 1
for k in ["q1","q2","q3","q4","q5","q6","q7","show_result"]:
    st.session_state.setdefault(k, None)

def step_indicator(step: int):
    total = 7
    st.progress(step/total, text=f"Adım {step}/{total}")

def next_step():
    st.session_state.step = min(7, st.session_state.step + 1)

def prev_step():
    st.session_state.step = max(1, st.session_state.step - 1)

def reset_all():
    st.session_state.step = 1
    for k in ["q1","q2","q3","q4","q5","q6","q7","show_result"]:
        st.session_state[k] = None

s = st.session_state

# Steps
if s.step == 1:
    step_indicator(1)
    s.q1 = st.radio("1) Lütfen cinsiyetinizi seçiniz.", ["Erkek","Kadin"], index=0 if s.q1 in (None,"Erkek") else 1, horizontal=True)
    st.button("İleri →", on_click=next_step)
elif s.step == 2:
    step_indicator(2)
    s.q2 = st.radio("2) Koşmayı planladığınız zemin türü nedir?", ["Road","Trail"], index=0 if s.q2 in (None,"Road") else 1, horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN: st.button("İleri →", on_click=next_step)
elif s.step == 3:
    step_indicator(3)
    s.q3 = st.radio("3) Koşu hedefiniz nedir?", ["Yaris","Antrenman"], index=0 if s.q3 in (None,"Yaris") else 1, horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN: st.button("İleri →", on_click=next_step)
elif s.step == 4:
    step_indicator(4)
    s.q4 = st.radio("4) Haftada kaç gün koşuyorsunuz?", ["3 ve daha az","4 ve daha fazla"], index=0 if s.q4 in (None,"3 ve daha az") else 1, horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN: st.button("İleri →", on_click=next_step)
elif s.step == 5:
    step_indicator(5)
    s.q5 = st.radio("5) Ortalama kaç km koşuyorsunuz? (her koşuda)", ["0-20 km","20 km ve daha fazla"], index=0 if s.q5 in (None,"0-20 km") else 1, horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN: st.button("İleri →", on_click=next_step)
elif s.step == 6:
    step_indicator(6)
    s.q6 = st.radio("6) Daha önce diz/kalça sakatlığı yaşadınız mı?", ["Var","Yok"], index=1 if s.q6 in (None,"Yok") else (0 if s.q6=="Var" else 1), horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN: st.button("İleri →", on_click=next_step)
elif s.step == 7:
    step_indicator(7)
    s.q7 = st.radio("7) Pronasyon (İçe basma) sorunu yaşıyor musunuz?", ["Evet","Hayir"], index=1 if s.q7 in (None,"Hayir") else (0 if s.q7=="Evet" else 1), horizontal=True)
    colB, colN = st.columns(2)
    with colB: st.button("← Geri", on_click=prev_step)
    with colN:
        if st.button("Sonucu Göster"):
            st.session_state.show_result = True

ready = all(s.get(k) is not None for k in ["q1","q2","q3","q4","q5","q6","q7"])
if ready and s.step == 7 and s.get("show_result"):
    params = dict(gender=s.q1, surface=s.q2, goal=s.q3, freq=s.q4, distance=s.q5, injury=s.q6, pronation=s.q7)
    filtered = apply_filters(dfn, params)
    show_cols = [c for c in out_cols if c in filtered.columns]

    st.subheader("Öneriler")
    st.caption(f"Toplam sonuç: {len(filtered)}")

    if len(filtered) == 0:
        st.warning("Sonuç bulunamadı. '← Geri' ile seçimlerinizi değiştirip tekrar deneyin.")
    else:
        st.dataframe(filtered[show_cols], use_container_width=True)
        csv = filtered[show_cols].to_csv(index=False).encode("utf-8")
        st.download_button("CSV indir", data=csv, file_name="intersport_running_footwear.csv", mime="text/csv")
    st.divider()
    if st.button("Baştan Başla"):
        reset_all()
