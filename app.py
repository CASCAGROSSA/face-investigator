import base64
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFont


st.set_page_config(
    page_title="Face Investigator Web",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Face Investigator Web")
st.caption("Versão web pronta para Streamlit Cloud")


def load_image(uploaded_file):
    return Image.open(uploaded_file).convert("RGB")


def image_signature(img: Image.Image):
    small = img.resize((32, 32)).convert("L")
    hist = small.histogram()
    avg = sum(i * v for i, v in enumerate(hist)) / max(sum(hist), 1)
    return avg


def compare_images(target_img: Image.Image, ref_img: Image.Image):
    t_sig = image_signature(target_img)
    r_sig = image_signature(ref_img)
    brightness_gap = abs(t_sig - r_sig)

    diff = ImageChops.difference(
        target_img.resize((256, 256)),
        ref_img.resize((256, 256))
    )
    diff_score = sum(diff.convert("L").histogram()[1:]) / (256 * 256)

    distance = (brightness_gap / 255.0) + (diff_score / 255.0)
    score = max(0.0, 1.0 - min(distance, 1.0))

    analysis = []
    if score > 0.85:
        analysis.append("Semelhança visual alta.")
    elif score > 0.70:
        analysis.append("Semelhança visual moderada.")
    else:
        analysis.append("Semelhança visual baixa.")

    if brightness_gap < 10:
        analysis.append("Brilho geral muito próximo.")
    elif brightness_gap < 25:
        analysis.append("Brilho geral próximo.")
    else:
        analysis.append("Brilho geral diferente.")

    return score, distance, analysis


def side_by_side(target_img: Image.Image, ref_img: Image.Image, title: str):
    target = target_img.copy().resize((320, 320))
    ref = ref_img.copy().resize((320, 320))
    canvas = Image.new("RGB", (660, 380), "white")
    canvas.paste(target, (20, 40))
    canvas.paste(ref, (340, 40))

    draw = ImageDraw.Draw(canvas)
    draw.text((20, 10), "ALVO", fill="black")
    draw.text((340, 10), title, fill="black")
    return canvas


with st.sidebar:
    st.header("Entradas")
    target_file = st.file_uploader(
        "Imagem alvo",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
    )

    reference_files = st.file_uploader(
        "Imagens de comparação",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )

    top_n = st.slider("Exibir no máximo", 1, 50, 10)

    run = st.button("Comparar", type="primary")


if run:
    if not target_file:
        st.error("Envie a imagem alvo.")
        st.stop()

    if not reference_files:
        st.error("Envie pelo menos uma imagem de comparação.")
        st.stop()

    target_img = load_image(target_file)
    results = []
    progress = st.progress(0, text="Processando imagens...")

    total = len(reference_files)
    for idx, ref_file in enumerate(reference_files, start=1):
        ref_img = load_image(ref_file)
        score, distance, analysis = compare_images(target_img, ref_img)
        results.append({
            "arquivo": ref_file.name,
            "score": score,
            "distancia": distance,
            "analise": " | ".join(analysis),
            "imagem": ref_img,
        })
        progress.progress(int(idx / total * 100), text=f"Processando {ref_file.name} ({idx}/{total})")

    progress.empty()

    df = pd.DataFrame(results).sort_values("score", ascending=False)

    st.success(f"{len(df)} correspondências processadas.")

    st.dataframe(
        df[["arquivo", "score", "distancia", "analise"]].head(top_n),
        use_container_width=True,
        hide_index=True,
    )

    csv_data = df[["arquivo", "score", "distancia", "analise"]].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV",
        data=csv_data,
        file_name="resultados_face_investigator.csv",
        mime="text/csv",
    )

    st.subheader("Comparações")
    for _, row in df.head(top_n).iterrows():
        st.markdown(f"### {row['arquivo']}")
        st.write(f"Score: {row['score']:.4f}  |  Distância: {row['distancia']:.4f}")
        st.write(row["analise"])
        preview = side_by_side(target_img, row["imagem"], row["arquivo"])
        st.image(preview, use_container_width=True)
else:
    st.info("Envie a imagem alvo e as imagens de comparação na barra lateral e clique em Comparar.")
