import streamlit as st
import pandas as pd
import altair as alt
import Orange
import pickle

st.set_page_config(
    page_title="Dashboard Analitik DJPb",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #f4f7fb;
    }
    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .dashboard-hero {
        padding: 2rem 2.25rem;
        margin-bottom: 1.5rem;
        border-radius: 20px;
        color: white;
        background: linear-gradient(120deg, #12304a 0%, #176b87 100%);
    }
    .dashboard-hero h1 {
        margin: 0;
        font-size: 2.25rem;
        color: white;
    }
    .dashboard-hero p {
        margin: 0.55rem 0 0;
        color: #d7e8f0;
        font-size: 1.05rem;
    }
    [data-testid="stMetric"] {
        padding: 1rem 1.15rem;
        border: 1px solid #e3eaf2;
        border-radius: 14px;
        background: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

data = pd.read_csv("data/02_realisasi_anggaran_klasifikasi.csv")


@st.cache_resource
def load_model():
    with open("models/Best_model.pkcls", "rb") as model_file:
        return pickle.load(model_file)


model = load_model()
jumlah_satker = len(data)
jumlah_tercapai = int(data["realisasi_tercapai_95persen"].eq("Ya").sum())
persentase_tercapai = jumlah_tercapai / jumlah_satker if jumlah_satker else 0

st.markdown(
    """
    <div class="dashboard-hero">
        <h1>Dashboard Analitik DJPb</h1>
        <p>Pantau kinerja, skor IKPA, dan pencapaian realisasi satker.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("DJPb")
    st.caption("Dashboard analitik kinerja satuan kerja")
    st.divider()
    st.metric("Satuan kerja", f"{jumlah_satker:,}")
    st.caption("Data klasifikasi realisasi anggaran")

tab_prediksi, tab_ringkasan, tab_visualisasi = st.tabs(["Prediksi", "Ringkasan", "Visualisasi"])

with tab_prediksi:
    st.header("Prediksi Realisasi 95%")
    st.markdown("Masukkan data input berikut dan klik tombol untuk melihat hasil prediksi.")

    col1, col2 = st.columns(2)
    with col1:
        jumlah_spm = st.number_input(
            "Jumlah SPM",
            min_value=1,
            max_value=200,
            value=10,
            step=1,
            format="%d",
        )
        revisi_dipa = st.number_input(
            "Revisi DIPA",
            min_value=0,
            max_value=5,
            value=1,
            step=1,
            format="%d",
        )
        deviasi_rpd_persen = st.number_input(
            "Deviasi RPD (%)",
            min_value=0.00,
            max_value=30.00,
            value=5.50,
            format="%.2f",
        )
    with col2:
        skor_ikpa = st.slider(
            "Skor IKPA",
            min_value=70.00,
            max_value=100.00,
            value=85.00,
            step=0.01,
            format="%.2f",
        )
        tipe_satker = st.selectbox(
            "Tipe Satker",
            ["Dekonsentrasi", "Kantor Daerah", "Kantor Pusat", "Tugas Pembantuan"],
        )

    if st.button("Prediksi", type="primary"):
        if model is None:
            st.error("Model belum tersedia.")
        else:
            tipe_values = [
                "Dekonsentrasi",
                "Kantor Daerah",
                "Kantor Pusat",
                "Tugas Pembantuan",
            ]
            tipe_indicators = [
                1.0 if tipe_satker == tipe_value else 0.0
                for tipe_value in tipe_values
            ]
            input_row = [
                float(jumlah_spm),
                float(revisi_dipa),
                float(deviasi_rpd_persen),
                float(skor_ikpa),
                *tipe_indicators,
            ]

            try:
                table = Orange.data.Table.from_list(model.domain, [input_row])
                prediction_index = int(model(table)[0])
                probabilities = model(table, model.Probs)[0]
                class_name = model.domain.class_var.values[prediction_index]
                confidence = float(probabilities[prediction_index])

                if class_name == "Ya":
                    st.success(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
                else:
                    st.warning(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
            except Exception as exc:
                st.error(f"Prediksi gagal dijalankan: {exc}")

with tab_ringkasan:
    st.subheader("Ringkasan kinerja")
    st.caption("Gambaran umum berdasarkan data realisasi anggaran yang tersedia.")
    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.metric("Total satuan kerja", f"{jumlah_satker:,}")
    kpi_2.metric(
        "Mencapai realisasi ≥95%",
        f"{persentase_tercapai:.1%}",
        f"{jumlah_tercapai:,} satuan kerja",
    )
    kpi_3.metric("Rata-rata skor IKPA", f"{data['skor_ikpa'].mean():.2f}")
    kpi_4.metric("Rata-rata deviasi RPD", f"{data['deviasi_rpd_persen'].mean():.2f}%")

with tab_visualisasi:
    st.subheader("Visualisasi data")
    st.caption("Pilih jenis grafik untuk menelusuri data kinerja satker.")
    tab_bubble, tab_pie, tab_bar, tab_histogram = st.tabs(
        ["Bubble Plot", "Diagram Pie", "Diagram Bar", "Histogram IKPA"]
    )

    with tab_bubble:
        st.header("Visualisasi Bubble Plot")
        st.markdown(
            "Grafik bubble menunjukkan skor IKPA terhadap deviasi RPD, dengan warna berdasarkan kolom `realisasi_tercapai_95persen`."
        )

        chart = (
            alt.Chart(data)
            .mark_circle(opacity=0.7, size=100)
            .encode(
                x=alt.X(
                    "skor_ikpa",
                    title="Skor IKPA",
                    scale=alt.Scale(domain=[70, 100]),
                ),
                y=alt.Y("deviasi_rpd_persen", title="Deviasi RPD (%)"),
                color=alt.Color(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                    scale=alt.Scale(
                        domain=["Tidak", "Ya"],
                        range=["#FF0000", "#FFD700"],
                    ),
                ),
                tooltip=[
                    "kode_satker",
                    "tipe_satker",
                    "skor_ikpa",
                    "deviasi_rpd_persen",
                    "realisasi_tercapai_95persen",
                ],
            )
            .properties(width=900, height=550)
            .interactive()
        )
        st.altair_chart(chart, width=900)

    with tab_pie:
        st.header("Proporsi Realisasi Tercapai 95%")
        pie_chart = (
            alt.Chart(data)
            .mark_arc()
            .encode(
                theta=alt.Theta("count():Q", title="Jumlah"),
                color=alt.Color(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                    scale=alt.Scale(
                        domain=["Tidak", "Ya"],
                        range=["#FF0000", "#FFD700"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "realisasi_tercapai_95persen:N",
                        title="Realisasi Tercapai 95%",
                    ),
                    alt.Tooltip("count():Q", title="Jumlah"),
                ],
            )
            .properties(width=500, height=400)
        )
        st.altair_chart(pie_chart, width="stretch")

    with tab_bar:
        st.header("Jumlah Realisasi Tercapai 95%")
        bar_chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                    sort=["Tidak", "Ya"],
                ),
                y=alt.Y("count():Q", title="Jumlah"),
                color=alt.Color(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                    scale=alt.Scale(
                        domain=["Tidak", "Ya"],
                        range=["#FF0000", "#FFD700"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "realisasi_tercapai_95persen:N",
                        title="Realisasi Tercapai 95%",
                    ),
                    alt.Tooltip("count():Q", title="Jumlah"),
                ],
            )
            .properties(width=500, height=400)
        )
        st.altair_chart(bar_chart, width="stretch")

    with tab_histogram:
        st.header("Sebaran Skor IKPA")
        histogram = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "skor_ikpa:Q",
                    bin=alt.Bin(maxbins=20),
                    title="Skor IKPA",
                ),
                y=alt.Y("count():Q", title="Jumlah"),
                color=alt.Color(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                    scale=alt.Scale(
                        domain=["Tidak", "Ya"],
                        range=["#FF0000", "#FFD700"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("count():Q", title="Jumlah"),
                    alt.Tooltip(
                        "realisasi_tercapai_95persen:N",
                        title="Realisasi Tercapai 95%",
                    ),
                ],
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(histogram, width="stretch")