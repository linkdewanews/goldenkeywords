import streamlit as st
import requests
import pandas as pd

# GANTI API KEY LO DI SINI
OPENROUTER_API_KEY = "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"
SERPAPI_KEY = "895c2655fc222ac3802aad5ab711835395f7f37a61672e467035d235793f6c85"

# === Estimasi Volume + Longtail Keyword ===
def estimate_volume_google(keyword):
    try:
        url = f"https://www.google.com/complete/search?client=firefox&q={keyword}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        suggestions = data[1]
        score = len(suggestions) * 10 + sum(len(s) for s in suggestions) // 10
        return score if score > 0 else 10, suggestions
    except:
        return 10, []

# === Ambil Allintitle pakai SerpAPI ===
def get_allintitle_serpapi(keyword):
    try:
        params = {
            "q": f'allintitle:"{keyword}"',
            "api_key": SERPAPI_KEY,
            "engine": "google"
        }
        res = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = res.json()
        return data.get("search_information", {}).get("total_results", 0)
    except:
        return 0

# === Hitung GKR (Google Keyword Ratio) ===
def categorize_gkr(gkr):
    if gkr <= 0.25:
        return "Wajib Digas!"
    elif gkr <= 0.75:
        return "Layak Perjuangan"
    elif gkr <= 1.0:
        return "Medium Kompetisi"
    else:
        return "Berat Bos!"

# === Generate 4 Meta Data Variasi via OpenRouter AI ===
def generate_meta_data(keyword):
    prompt = f"""
Buatkan minimal 4 variasi untuk topik '{keyword}' dalam bahasa Indonesia. fokus untuk branding website judi online, slot, casino, poker, dan taruhan bola.
    Tiap variasi berisi:
    tittle : Panjang Ideal: Usahakan antara 50-60 karakter (termasuk spasi), Relevansi: Judul harus secara akurat mencerminkan konten halaman, Kata Kunci Utama di Awal: Sebisa mungkin, letakkan kata kunci utama di bagian awal judul, Unik: Setiap halaman di website Anda sebaiknya memiliki title tag yang unik, Menarik Perhatian: Selain relevan dan mengandung kata kunci, judul juga harus menarik perhatian pengguna di hasil pencarian sehingga mereka tertarik untuk mengklik, Cantumkan Nama Brand (Opsional): Jika relevan dan masih ada ruang, Anda bisa menambahkan nama brand di bagian akhir judul, dipisahkan dengan tanda "|", "-", atau ":".
    keywords : (5 keyword SEO relevan, pisahkan dengan koma)
    deskripsi : Panjang Ideal: Usahakan antara 150-160 karakter (termasuk spasi). Google biasanya menampilkan deskripsi sepanjang ini, Ringkasan Konten: Meta deskripsi harus memberikan ringkasan singkat dan menarik tentang isi halaman, Kata Kunci Relevan: Sertakan kata kunci utama dan kata kunci terkait secara alami dalam deskripsi, Ajakan Bertindak (Call to Action): Dorong pengguna untuk mengklik dengan menyertakan ajakan bertindak yang jelas (misalnya: "Pelajari lebih lanjut", "Temukan rahasianya di sini", "Baca panduan lengkapnya"), Manfaat atau Solusi: Tekankan manfaat yang akan didapatkan pengguna jika mereka mengunjungi halaman Anda atau solusi yang Anda tawarkan untuk masalah mereka, Unik: Sama seperti title tag, setiap halaman sebaiknya memiliki meta deskripsi yang unik, Hindari Clickbait: Meskipun harus menarik, hindari membuat deskripsi yang menyesatkan atau tidak sesuai dengan isi halaman (clickbait).

    Fokus utama Anda saat ini adalah membuat title tag yang relevan, mengandung kata kunci utama di awal, unik, menarik, dan tidak terlalu panjang. Kemudian, buatlah meta description tag yang merangkum konten, mengandung kata kunci relevan secara alami, mendorong klik dengan ajakan bertindak atau menyoroti manfaat, unik, dan tidak terlalu panjang. 

    Format output:
    === VARIASI 1 ===
    tittle : ...
    keywords : ...
    deskripsi : ...

    === VARIASI 2 ===
    ... dst
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generate meta data: {e}"

# === Streamlit UI ===
st.set_page_config(page_title="GKR Checker + Meta Generator", layout="wide")
page = st.selectbox("Pilih Halaman:", ["Cek GKR", "Generate Meta Data", "Tentang Tools Ini"])

if "history_meta" not in st.session_state:
    st.session_state["history_meta"] = []

if page == "Cek GKR":
    st.title("GKR Checker")
    keywords_input = st.text_area("Masukkan keyword (satu per baris):", height=150)

    if st.button("Jalankan Analisa"):
        if not keywords_input.strip():
            st.warning("Masukkan keyword dulu bre!")
        else:
            keywords = [kw.strip() for kw in keywords_input.split("\n") if kw.strip()]
            results = []

            for kw in keywords:
                with st.spinner(f"Analisa keyword: {kw}"):
                    volume, suggestions = estimate_volume_google(kw)
                    allintitle = get_allintitle_serpapi(kw)
                    gkr = allintitle / volume if volume else 999
                    kategori = categorize_gkr(gkr)
                    results.append({
                        "Keyword": kw,
                        "Volume": volume,
                        "Allintitle": allintitle,
                        "GKR": round(gkr, 2),
                        "Kategori": kategori,
                        "Longtail": ", ".join(suggestions[:3]) if suggestions else "-"
                    })

            df = pd.DataFrame(results)
            st.session_state["gkr_result"] = df
            st.subheader("Hasil Analisa")
            st.dataframe(df, use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False), file_name="gkr_result.csv")

elif page == "Generate Meta Data":
    st.title("Generator Judul, Deskripsi & Keyword (OpenRouter AI)")
    if "gkr_result" not in st.session_state:
        st.info("Belum ada hasil GKR. Jalankan dulu di halaman sebelumnya.")
    else:
        df = st.session_state["gkr_result"]
        pilihan = df[df["Kategori"] == "Wajib Digas!"]["Keyword"].tolist()

        if not pilihan:
            st.warning("Belum ada keyword GKR rendah.")
        else:
            selected = st.selectbox("Pilih keyword terbaik:", pilihan)
            if st.button("Generate Meta Data"):
                with st.spinner("Lagi generate meta data dari OpenRouter..."):
                    meta = generate_meta_data(selected)
                    st.session_state["history_meta"].insert(0, {"keyword": selected, "output": meta})
                    st.session_state["history_meta"] = st.session_state["history_meta"][:20]
                    st.subheader(f"Meta Data: {selected}")
                    st.code(meta)
                    st.download_button("Download Output", meta, file_name=f"{selected}_meta.txt")

            if st.session_state["history_meta"]:
                st.subheader("Riwayat Meta Data (Max 20 Terakhir)")
                for item in st.session_state["history_meta"]:
                    with st.expander(f"{item['keyword']}"):
                        st.code(item['output'])

elif page == "Tentang Tools Ini":
    st.title("Tentang Tools Ini")
    st.markdown("""
**GKR + Meta Generator Tools**  
Tools SEO serba guna buat riset keyword + auto generate konten metadata (judul, deskripsi, keyword).

- Estimasi Volume via Google Suggest
- Allintitle Check via SerpAPI
- GKR Ratio (Google Keyword Ratio)
- Auto Meta Generator (via OpenRouter AI)

Mantap buat autoblog, micro niche, content farming
    """)
