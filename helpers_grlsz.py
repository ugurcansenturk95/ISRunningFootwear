
import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata, re, io

# -----------------------------
# Text utils
# -----------------------------
def strip_accents(s: str) -> str:
    s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def norm_token(s: str) -> str:
    s = strip_accents(str(s)).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

# -----------------------------
# Column pick & normalization
# -----------------------------
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

# -----------------------------
# Excel column letters -> names
# -----------------------------
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
    """
    Kurallar:
    - Q1: gender -> 'erkek' / 'kadin'
    - Q2: surface -> 'road' / 'trail'
    - Q3: goal -> 'yaris' / 'antrenman'
    - Q4: freq -> '4 ve daha fazla' ise q4_is_long == True
    - Q5: distance -> '20 km ve daha fazla' ise q5_group ∈ {'orta mesafe','uzun mesafe'}
    - Q6: injury -> 'Var' ise q6_injury_ok == True
    - Q7: pronation -> 'Evet' ise q7_pronation_yes == True
    """
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

# -----------------------------
# URL helpers (for Streamlit Cloud secrets)
# -----------------------------
def fix_cloud_link(u: str) -> str:
    if not isinstance(u, str):
        return u
    url = u.strip()
    m = re.search(r"drive\.google\.com/file/d/([^/]+)/", url)
    if m:  # Google Drive page -> direct download
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
    # Fallback guess
    try:
        bio.seek(0)
        return pd.read_excel(bio, sheet_name="Data")
    except Exception:
        bio.seek(0)
        return pd.read_csv(bio)

# -----------------------------
# Main loader with secrets support
# -----------------------------
def load_df(preferred_names=None):
    if preferred_names is None:
        preferred_names = ["Kod _n_ son grlsz.xlsx", "Kod _n_ son.xlsx", "Kod Önü son.xlsx", "data.xlsx"]

    # 1) Secrets: DATA_URL (forces no uploader)
    if hasattr(st, "secrets"):
        url = st.secrets.get("DATA_URL", "").strip()
        if url:
            try:
                df_raw = load_from_url(url)
                return df_raw, "Secrets: DATA_URL"
            except Exception as e:
                st.error(f"DATA_URL indirilemedi: {e}")

        # 2) Secrets: DATA_FILE (exact repo path or filename)
        data_file = st.secrets.get("DATA_FILE", "").strip()
        if data_file:
            p = Path(data_file)
            if not p.exists():
                # try relative to repo root
                p = Path(".") / data_file
            if p.exists():
                try:
                    df_raw = pd.read_excel(p, sheet_name="Data")
                    return df_raw, f"Secrets: DATA_FILE ({p.name}) (Data)"
                except Exception:
                    df_raw = pd.read_excel(p, sheet_name="DATA")
                    return df_raw, f"Secrets: DATA_FILE ({p.name}) (DATA)"
            else:
                st.error(f"DATA_FILE bulunamadı: {data_file}")

    # 3) Local files with preferred names
    candidates = [Path(name) for name in preferred_names] + [Path("/mnt/data") / name for name in preferred_names]
    data_path = next((p for p in candidates if p.exists()), None)
    if data_path is not None:
        try:
            df_raw = pd.read_excel(data_path, sheet_name="Data")
            return df_raw, f"Yerel: {data_path.name} (Data)"
        except Exception:
            df_raw = pd.read_excel(data_path, sheet_name="DATA")
            return df_raw, f"Yerel: {data_path.name} (DATA)"

    # 4) Fallback: file uploader
    uploaded = st.file_uploader("Excel yükle (.xlsx) — Data/DATA sayfası olmalı", type=["xlsx"])
    if uploaded is not None:
        try:
            df_raw = pd.read_excel(uploaded, sheet_name="Data")
            return df_raw, "Yüklenen dosya (Data)"
        except Exception:
            uploaded.seek(0)
            df_raw = pd.read_excel(uploaded, sheet_name="DATA")
            return df_raw, "Yüklenen dosya (DATA)"

    st.info("Aynı klasöre 'Kod _n_ son grlsz.xlsx' koyun, ya da Secrets -> DATA_URL / DATA_FILE ayarlayın, ya da Excel yükleyin.")
    st.stop()
