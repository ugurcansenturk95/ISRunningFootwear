
# Intersport Running Footwear — Full Starter (Wizard + Simple)

Bu repo, **Streamlit Cloud** ve yerel kullanım için hazır uygulama paketidir.
- `running_shoes_app_grlsz_wizard.py` → Sorular **sıra ile** gelen sürüm (**önerilen ana dosya**)
- `running_shoes_app_grlsz_simple.py` → Tüm sorular tek sayfada
- `running_shoes_app_v4f.py` → Wizard + URL desteği (alternatif ana dosya)
- `app_public_wizard_v2_url.py` → URL odaklı minimal wizard (alternatif)
- `helpers_grlsz.py` → Ortak fonksiyonlar (**DATA_URL / DATA_FILE secrets desteği**)
- `requirements.txt` → Bağımlılıklar

## Kurallar (özet)
- Q1..Q7 soruları yanıtlanır.
- Filtreler uygulanır; sonuçta **B, C, D, H, K, L, M, N, O, P** sütunları gösterilir.
- CSV indirme düğmesi vardır.

---

## 1) Yerelde Çalıştırma
```bat
pip install -r requirements.txt
streamlit run running_shoes_app_grlsz_wizard.py
```
- Aynı klasörde **`Kod _n_ son grlsz.xlsx`** varsa (Data/DATA sayfası) otomatik okunur.
- Yoksa uygulama **Excel yükle (.xlsx)** alanı gösterir.

> Windows için `python -m pip install ...` ve `python -m streamlit run ...` da kullanabilirsin.

---

## 2) GitHub’a Yükleme
### A) Tarayıcıdan (kolay)
1. GitHub → **New repository** → ad: `intersport-running-footwear` → **Public** → Create
2. Repo → **Add file → Upload files**
3. Bu klasörün içindeki **tüm dosyaları** sürükleyip bırak → **Commit changes**

### B) Komut satırı (opsiyonel)
```bat
cd C:\proj\intersport
git init
git remote add origin https://github.com/<kullanici-adin>/intersport-running-footwear.git
git add .
git commit -m "first deploy"
git branch -M main
git push -u origin main
```

---

## 3) Streamlit Cloud’a Deploy
1. https://streamlit.io/cloud → **Sign in with GitHub**
2. **New app** → repo: `intersport-running-footwear`
3. **Branch:** `main`
4. **Main file:** `running_shoes_app_grlsz_wizard.py`  (önerilen)
5. **Deploy**

Oluşan URL’yi telefonunda açabilir, paylaşabilirsin.

---

## 4) Excel’i Sürekli Yükletmemek (Secrets ile otomatik)
**helpers_grlsz.py** secrets destekli. Streamlit Cloud’da **Settings → Secrets** bölümüne aşağıdakilerden **birini** ekle:

### Seçenek 1 — URL’den indir (önerilen)
```toml
DATA_URL = "https://drive.google.com/file/d/FILE_ID/view?usp=sharing"
```
- Drive linki otomatik `uc?export=download&id=...` formatına çevrilir.
- Dropbox `...?dl=0` → otomatik `?raw=1`
- OneDrive → otomatik `download=1`

### Seçenek 2 — Repo içindeki dosya
```toml
DATA_FILE = "Kod _n_ son grlsz.xlsx"
```
veya alt klasördeyse:
```toml
DATA_FILE = "data/Kod_n_son_grlsz.xlsx"
```

> Secrets ayarlıysa **yükleme alanı görünmez**; veri **otomatik** yüklenir.

---

## 5) Sık Karşılaşılan Sorunlar
- **App file not found** → Cloud’da **Main file** yolunu doğru seç (wizard/simple/v4f).
- **ModuleNotFoundError** → `requirements.txt` repo’da mı? Doğru yazıldı mı? Deploy’u yenile.
- **Sheet bulunamadı** → Excel’de sayfa adı `Data` veya `DATA` olmalı.
- **Path hatası (WindowsPath + WindowsPath)** → Kod güncel; join işlemi `Path('/mnt/data') / name` olarak düzeltildi.
- **403/404 indirme** → URL public mi? (Drive/Dropbox/OneDrive paylaşım modu: herkes görebilir/indirilebilir.)

---

*Paket oluşturma zamanı: 20250824_192928*
