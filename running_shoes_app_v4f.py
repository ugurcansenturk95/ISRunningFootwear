
import streamlit as st
import pandas as pd
import io, re, unicodedata
from pathlib import Path

st.set_page_config(page_title="Intersport Running Footwear", layout="centered")
st.title("Intersport Running Footwear")

# -----------------------------
# Helpers
# -----------------------------
def strip_accents(s: str) -> str:
    s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def norm_token(s: str) -> str:
    s = strip_accents(str(s)).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def pick(df: pd.DataFrame, key):
    if key in df.columns:
        return df[key]
    if isinstance(key, int) and str(key) in df.columns:
        return df[str(key)]
    return pd.Series([None]*len(df), index=df.index)

def build_normalized_view(df: pd.DataFrame) -> pd.DataFrame:
    dfn = df.copy()
    c1 = pick(dfn, 1).astype(str)
    c2 = pick(dfn, 2).astype(str)
    c3 = pick(dfn, 3).astype(str)
    c4 = pick(dfn, 4).astype(str)
    c5 = pick(dfn, 5).astype(str)
    c6 = pick(dfn, 6)
    c7 = pick(dfn, 7).astype(str)

    # Q1: Gender
    dfn["q1"] = c1.map(lambda x: "erkek" if "erkek" in norm_token(x) or "male" in norm_token(x) else ("kadin" if "kadin" in norm_token(x) or "female" in norm_token(x) else None))

    # Q2: Surface
    def map_surface(x):
        t = norm_token(x)
        if "yol" in t or "road" in t:
            return "road"
        if "patika" in t or "trail" in t:
            return "trail"
        return None
    dfn["q2"] = c2.map(map_surface)

    # Q3: Goal
    def map_goal(x):
        t = norm_token(x)
        if "yaris" in t or "race" in t:
            return "yaris"
        if "antrenman" in t or "training" in t:
            return "antrenman"
        return None
    dfn["q3"] = c3.map(map_goal)

    # Q4: Durability long
    def map_durability_long(x):
        t = norm_token(x)
        return ("uzun" in t) and ("omurlu" in t or "omur" in t)
    dfn["q4_is_long"] = c4.map(map_durability_long)

    # Q5: Distance group
    def map_distance_group(x):
        t = norm_token(x)
        if ("orta" in t and "mesafe" in t) or ("medium" in t):
            return "orta mesafe"
        if ("uzun" in t and "mesafe" in t) or ("long" in t):
            return "uzun mesafe"
        if ("kisa" in t and "mesafe" in t) or ("short" in t):
            return "kisa mesafe"
        return None
    dfn["q5_group"] = c5.map(map_distance_group)

    # Q6: Injury ok
    def map_injury_ok(x):
        try:
            xv = float(x)
            return abs(xv - 1.2) < 1e-6
        except Exception:
            t = norm_token(str(x))
            return ("evet" in t) or ("uygun" in t) or ("yes" in t)
    dfn["q6_injury_ok"] = c6.map(map_injury_ok)

    # Q7: Pronation yes
    def map_pronation_yes(x):
        t = norm_token(x)
        return ("evet" in t) or (t == "1") or ("yes" in t)
    dfn["q7_pronation_yes"] = c7.map(map_pronation_yes)

    return dfn

def excel_letter_to_name(cols, letter: str) -> str:
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    val = 0
    for ch in letter:
        val = val * 26 + (alpha.index(ch.upper()) + 1)
    idx = val - 1
    if idx < 0 or idx >= len(cols):
        raise IndexError(f"Column letter {letter} is out of range for this sheet.")
    return str(cols[idx])

def resolve_output_columns(df: pd.DataFrame):
    # Required set: B, C, D, H, K, L, M, N, O, P
    letters = ["B","C","D","H","K","L","M","N","O","P"]
    names = []
    for L in letters:
        try:
            name = excel_letter_to_name(df.columns, L)
            if name in df.columns:
                names.append(name)
        except Exception:
            pass
    return names

def apply_filters(df_norm: pd.DataFrame, params: dict) -> pd.DataFrame:
    f = df_norm.copy()
    f = f[f["q1"] == ("erkek" if params["gender"] == "Erkek" else "kadin")]
    f = f[f["q2"] == ("road" if params["surface"] == "Road" else "trail")]
    f = f[f["q3"] == ("yaris" if params["goal"] == "Yaris" else "antrenman")]
    if params["freq"] == "4 ve daha fazla":
        f = f[f["q4_is_long"] == True]
    if params["distance"] == "20 km ve daha fazla":
        f = f[f["q5_group"].isin(["orta mesafe", "uzun mesafe"])]
    if params["injury"] == "Var":
        f = f[f["q6_injury_ok"] == True]
    if params["pronation"] == "Evet":
        f = f[f["q7_pronation_yes"] == True]
    return f

def fix_cloud_link(u: str) -> str:
    if not isinstance(u, str):
        return u
    url = u.strip()
    m = re.search(r"drive\.google\.com/file/d/([^/]+)/", url)
    if m:  # Google Drive file page -> direct download
        fid = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={fid}"
    m = re.search(r"drive\.google\.com/open\?id=([^&]+)", url)
    if m:
        fid = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={fid}"
    if "dropbox.com" in url and "raw=1" not in url:
        if "dl=0" in url:
            url = url.replace("dl=0", "raw=1")
        elif "raw=1" not in url:
            sep = "&" if "?" in url else "?"
            url = url + f"{sep}raw=1"
    if "1drv.ms" in url or "onedrive.live.com" in url:
        if "download=1" not in url:
            sep = "&" if "?" in url else "?"
            url = url + f"{sep}download=1"
    return url

@st.cache_data(show_spinner=False)
def fetch_bytes(url: str) -> bytes:
    import requests
    url = fix_cloud_link(url)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content

def load_from_url(url: str) -> pd.DataFrame:
    data = fetch_bytes(url)
    low = url.lower()
    bio = io.BytesIO(data)
    if any(low.endswith(ext) for ext in [".xlsx",".xlsm",".xls"]):
        try:
            return pd.read_excel(bio, sheet_name="Data")
        except Exception:
            bio.seek(0)
            return pd.read_excel(bio, sheet_name="DATA")
    if any(low.endswith(ext) for ext in [".csv",".csv.gz",".txt"]):
        bio.seek(0)
        return pd.read_csv(bio)
    try:
        bio.seek(0)
        return pd.read_excel(bio, sheet_name="Data")
    except Exception:
        bio.seek(0)
        return pd.read_csv(bio)

# -----------------------------
# Data loading (prefer 'Kod _n_ son grlsz.xlsx')
# -----------------------------
preferred_names = ["Kod _n_ son grlsz.xlsx", "Kod _n_ son.xlsx", "Kod Önü son.xlsx", "data.xlsx"]
candidates = [Path(name) for name in preferred_names] + [Path("/mnt/data/")+Path(name) for name in preferred_names]
data_path = next((p for p in candidates if p.exists()), None)

st.markdown("#### Veri Kaynağı")
df_raw = None
source_label = None

if data_path is not None:
    try:
        df_raw = pd.read_excel(data_path, sheet_name="Data")
        source_label = f"Yerel: {data_path.name} (Data)"
    except Exception:
        df_raw = pd.read_excel(data_path, sheet_name="DATA")
        source_label = f"Yerel: {data_path.name} (DATA)"

if df_raw is None:
    data_url = st.text_input("Opsiyonel: Public veri URL'si (Drive/Dropbox/OneDrive/GitHub Releases vb.)", value="", placeholder="https://drive.google.com/file/d/FILE_ID/view?usp=sharing")
    uploaded = st.file_uploader("Ya da Excel yükle (.xlsx)", type=["xlsx"], accept_multiple_files=False)
    if data_url.strip():
        try:
            with st.spinner("URL'den veri indiriliyor..."):
                df_raw = load_from_url(data_url.strip())
                source_label = "URL'den yüklendi"
        except Exception as e:
            st.error(f"URL'den yüklenemedi: {e}")
    if df_raw is None and uploaded is not None:
        try:
            df_raw = pd.read_excel(uploaded, sheet_name="Data")
            source_label = "Yüklenen dosya (Data)"
        except Exception:
            uploaded.seek(0)
            df_raw = pd.read_excel(uploaded, sheet_name="DATA")
            source_label = "Yüklenen dosya (DATA)"

if df_raw is None:
    st.info("Aynı klasöre 'Kod _n_ son grlsz.xlsx' koyun ya da URL/dosya yükleyin.")
    st.stop()

st.caption(f"Kaynak: {source_label}")

# -----------------------------
# Core logic
# -----------------------------
dfn = build_normalized_view(df_raw)
out_cols = resolve_output_columns(df_raw)

# Wizard state
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

with st.sidebar:
    if st.button("Sıfırla"):
        reset_all()

s = st.session_state

# Steps (sequential)
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

# Results
ready = all(s.get(k) is not None for k in ["q1","q2","q3","q4","q5","q6","q7"])
if ready and s.step == 7 and s.get("show_result"):
    params = dict(gender=s.q1, surface=s.q2, goal=s.q3, freq=s.q4, distance=s.q5, injury=s.q6, pronation=s.q7)
    filtered = apply_filters(build_normalized_view(df_raw), params)
    out_cols = resolve_output_columns(df_raw)
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
