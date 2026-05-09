import io
import pandas as pd
import streamlit as st
from PIL import Image, ImageChops


st.set_page_config(
    page_title="Face Investigator Web",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Face Investigator Web")
st.caption("Versão web estável para Streamlit Cloud")


if "processed" not in st.session_state:
    st.session_state.processed = False

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if "target_name" not in st.session_state:
    st.session_state.target_name = None


def open_image(uploaded_file):
    uploaded_file.seek(0)
    return Image.open(uploaded_file).convert("RGB")


def make_thumb(image, size=(72, 72)):
    thumb = image.copy()
    thumb.thumbnail(size)
    return thumb


def compare_images_simple(target_img, ref_img):
    a = target_img.resize((128, 128)).convert("L")
    b = ref_img.resize((128, 128)).convert("L")

    diff = ImageChops.difference(a, b)
    hist = diff.histogram()

    total_pixels = 128 * 128
    weighted_sum = sum(value * count for value, count in enumerate(hist))
    mean_diff = weighted_sum / total_pixels

    distance = mean_diff / 255.0
    score = max(0.0, 1.0 - distance)

    if score >= 0.85:
        status = "Alta semelhança"
    elif score >= 0.70:
        status = "Semelhança moderada"
    else:
        status = "Baixa semelhança"

    return round(score, 4), round(distance, 4), status


with st.form("face_form"):
    st.subheader("Entradas")

    target_file = st.file_uploader(
        "Imagem alvo",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False
    )

    reference_files = st.file_uploader(
        "Imagens de comparação",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    submitted = st.form_submit_button("Processar comparação")


if target_file:
    target_preview = open_image(target_file)
    st.markdown("### Prévia da imagem alvo")
    st.image(make_thumb(target_preview), caption=target_file.name, width=72)

if reference_files:
    st.markdown("### Prévia das imagens de comparação")
    cols = st.columns(min(6, len(reference_files)))
    for i, ref in enumerate(reference_files):
        ref_preview = open_image(ref)
        with cols[i % len(cols)]:
            st.image(make_thumb(ref_preview), caption=ref.name, width=72)

if submitted:
    if not target_file:
        st.error("Envie a imagem alvo.")
        st.stop()

    if not reference_files:
        st.error("Envie pelo menos uma imagem de comparação.")
        st.stop()

    target_img = open_image(target_file)

    results = []
    progress = st.progress(0, text="Processando comparação...")
    total = len(reference_files)

    for idx, ref in enumerate(reference_files, start=1):
        ref_img = open_image(ref)
        score, distance, status = compare_images_simple(target_img, ref_img)

        results.append({
            "arquivo": ref.name,
            "score": score,
            "distancia": distance,
            "classificacao": status
        })

        progress.progress(
            int(idx / total * 100),
            text=f"Processando {ref.name} ({idx}/{total})"
        )

    progress.empty()

    df = pd.DataFrame(results).sort_values(
        by=["score", "distancia"],
        ascending=[False, True]
    ).reset_index(drop=True)

    st.session_state.processed = True
    st.session_state.results_df = df
    st.session_state.target_name = target_file.name

if st.session_state.processed and st.session_state.results_df is not None:
    st.success("Comparação concluída com sucesso.")

    st.write(f"Imagem alvo: {st.session_state.target_name}")
    st.write(f"Total processado: {len(st.session_state.results_df)}")

    st.markdown("### Ranking")
    st.dataframe(
        st.session_state.results_df,
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = st.session_state.results_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Baixar resultados CSV",
        data=csv_bytes,
        file_name="face_investigator_resultados.csv",
        mime="text/csv"
    )
else:
    st.info("Envie a imagem alvo, selecione as imagens de comparação e clique em Processar comparação.")
