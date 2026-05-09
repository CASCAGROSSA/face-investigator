import streamlit as st
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Face Investigator Web", page_icon="🧠", layout="wide")

st.title("🧠 Face Investigator Web")
st.caption("Versão web estável para Streamlit Cloud")

target_file = st.file_uploader("Imagem alvo", type=["jpg", "jpeg", "png"])
reference_files = st.file_uploader(
    "Imagens de comparação",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if target_file and reference_files:
    st.success("Imagens carregadas com sucesso.")
    st.write(f"Imagem alvo: {target_file.name}")
    st.write(f"Total de imagens de comparação: {len(reference_files)}")

    rows = []
    for ref in reference_files:
        rows.append({"arquivo": ref.name, "status": "recebido"})

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.image(Image.open(target_file), caption="Imagem alvo", use_container_width=True)

    for ref in reference_files[:3]:
        st.image(Image.open(ref), caption=ref.name, use_container_width=True)
else:
    st.info("Envie a imagem alvo e pelo menos uma imagem de comparação.")
