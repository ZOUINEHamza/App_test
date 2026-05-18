import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="SigNoise Viewer", layout="wide", page_icon="📡")

# Style personnalisé
st.markdown("""
    <style>
    .main { background-color: #F7F7F5; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 SigNoise : Portail de Consultation")
st.markdown("---")

# 1. Gestion des fichiers JSON
archive_dir = "archives"
if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

# Liste des fichiers JSON dans le dossier archives/
json_files = [f for f in os.listdir(archive_dir) if f.endswith(".json")]

data = None

if not json_files:
    st.sidebar.warning("Aucun fichier .json trouvé dans le dossier 'archives'.")
    uploaded = st.file_uploader("Importez un fichier JSON généré par SigNoise", type="json")
    if uploaded:
        data = json.load(uploaded)
else:
    st.sidebar.header("🔍 Historique")
    selected_file = st.sidebar.selectbox("Choisir un traitement", json_files)
    
    with open(os.path.join(archive_dir, selected_file), 'r') as f:
        data = json.load(f)
    
    st.sidebar.info(f"Fichier chargé : {selected_file}")

if data:
    # 2. Affichage des indicateurs
    st.subheader(f"Résultats : {data.get('id', 'N/A')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Date du test", data.get("date", "N/A"))
    c2.success(f"Émetteur : {data.get('decision', 'Inconnu')}")
    c3.metric("Confiance IA", data.get("confiance", "0%"))

    st.markdown("---")

    # 3. Reconstruction des graphiques
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📊 Densité Spectrale (PSD)")
        try:
            psd_f = np.array(data["psd"]["f"])
            psd_p = np.array(data["psd"]["p"])
            
            # Centrage du spectre pour l'affichage (Shift)
            f_shift = np.fft.fftshift(psd_f) / 1000  # kHz
            p_shift = np.fft.fftshift(psd_p)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=f_shift, y=p_shift, mode='lines', line=dict(color='#185FA5')))
            fig.update_layout(xaxis_title="Fréquence (kHz)", yaxis_title="Puissance (dB)", 
                              template="plotly_white", height=450)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur graphique PSD : {e}")

    with col_right:
        st.markdown("### 📈 Variance d'Allan (AVAR)")
        try:
            avar_x = np.array(data["avar"]["x"])
            avar_y = np.array(data["avar"]["y"])
            
            fig2 = go.Figure()
            # On affiche Sigma (racine carrée de la variance)
            fig2.add_trace(go.Scatter(x=avar_x, y=np.sqrt(avar_y), mode='lines+markers', line=dict(color='#1D9E75')))
            fig2.update_layout(xaxis_type="log", yaxis_type="log", 
                               xaxis_title="Tau (s)", yaxis_title="Sigma (Stabilité)",
                               template="plotly_white", height=450)
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur graphique AVAR : {e}")
else:
    st.info("👋 En attente de données. Veuillez sélectionner un fichier dans l'historique ou en importer un.")

st.sidebar.markdown("---")
st.sidebar.info("PFE 2025/2026 - École Navale")
