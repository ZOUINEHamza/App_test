import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="SigNoise Viewer Pro", layout="wide", page_icon="📡")

# Style CSS identique à l'app desktop
st.markdown("""
    <style>
    .main { background-color: #F7F7F5; }
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; }
    .stMetric { 
        background-color: white; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-top: 4px solid #1D9E75;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 SigNoise : Dashboard d'Identification Cloud")
st.markdown("---")

# 1. Gestion des fichiers JSON
archive_dir = "archives"
if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

json_files = [f for f in os.listdir(archive_dir) if f.endswith(".json")]
data = None

# Sidebar
st.sidebar.header("🔍 Historique")
if json_files:
    selected_file = st.sidebar.selectbox("Sélectionner un traitement", sorted(json_files, reverse=True))
    with open(os.path.join(archive_dir, selected_file), 'r') as f:
        data = json.load(f)
else:
    st.sidebar.warning("Dossier 'archives' vide.")
    uploaded = st.file_uploader("Importer un fichier JSON complet", type="json")
    if uploaded:
        data = json.load(uploaded)

if data:
    # --- EN-TÊTE ---
    st.header(f"Rapport d'Identification : {data['id']}")
    
    # --- MÉTRIQUES ---
    m = data.get("metrics", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bursts Connus", m.get("n_connus", 0))
    c2.metric("Bursts Inconnus", m.get("n_inconnus", 0), delta_color="inverse")
    c3.metric("Total Bursts", m.get("n_total", 0))
    c4.metric("Temps de calcul", f"{m.get('elapsed', 0)}s")

    st.markdown("---")

    # --- DISTRIBUTION ET PROBABILITÉS ---
    col_dist, col_prob = st.columns([1, 1])

    with col_dist:
        st.subheader("Distribution des émetteurs")
        dist = data.get("distribution", {})
        if dist:
            labels = list(dist.keys())
            values = list(dist.values())
            # Ajouter inconnus si présents
            if m.get("n_inconnus", 0) > 0:
                labels.append("INCONNUS")
                values.append(m.get("n_inconnus", 0))
            
            fig_dist = go.Figure(data=[go.Bar(
                x=labels, y=values,
                text=values, textposition='auto',
                marker_color=['#1D9E75' if l != "INCONNUS" else '#D85A30' for l in labels]
            )])
            fig_dist.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), height=350)
            st.plotly_chart(fig_dist, use_container_width=True)

    with col_prob:
        st.subheader("Probabilités par classe")
        # On affiche la classe gagnante et sa confiance
        st.success(f"DÉCISION FINALE : **{data['decision']}**")
        st.info(f"CONFIANCE IA : **{data['confiance']}**")
        st.write(f"Date du traitement : {data['date']}")

    # --- TABLEAUX ---
    col_t1, col_t2 = st.columns([1.5, 1])
    
    with col_t1:
        st.subheader("📋 Détail des Bursts détectés")
        bursts = data.get("bursts", {})
        if bursts:
            df_bursts = pd.DataFrame({
                "Burst #": range(1, len(bursts["labels"]) + 1),
                "Classe prédite": bursts["labels"],
                "Probabilité (%)": bursts["probas"],
                "Statut": ["✅ Connu" if l != "INCONNU" else "❓ Inconnu" for l in bursts["labels"]]
            })
            st.dataframe(df_bursts, use_container_width=True, height=300, hide_index=True)

    with col_t2:
        st.subheader("🕵️ Groupes Inconnus")
        groupes = data.get("groupes_inconnus", {})
        if groupes:
            uids = list(groupes.keys())
            counts = [g["n"] for g in groupes.values()]
            status = [g.get("statut", "EN_ATTENTE") for g in groupes.values()]
            df_inc = pd.DataFrame({
                "Groupe": uids,
                "Nb bursts": counts,
                "Statut": status
            })
            st.table(df_inc)
        else:
            st.write("Aucun groupe inconnu détecté.")

    st.markdown("---")

    # --- ANALYSE SIGNAL ---
    st.header("🔬 Analyse Spectrale et Stabilité")
    tab_psd, tab_avar = st.tabs(["Densité Spectrale (PSD)", "Variance d'Allan (AVAR)"])

    with tab_psd:
        try:
            f = np.fft.fftshift(data["psd"]["f"]) / 1000
            p = np.fft.fftshift(data["psd"]["p"])
            fig_psd = go.Figure(go.Scatter(x=f, y=p, mode='lines', line=dict(color='#185FA5')))
            fig_psd.update_layout(xaxis_title="Fréquence (kHz)", yaxis_title="Puissance (dB)", 
                                 template="plotly_white", height=500)
            st.plotly_chart(fig_psd, use_container_width=True)
        except: st.error("Données PSD manquantes.")

    with tab_avar:
        try:
            ax = data["avar"]["x"]
            ay = np.sqrt(data["avar"]["y"])
            fig_avar = go.Figure(go.Scatter(x=ax, y=ay, mode='lines+markers', line=dict(color='#1D9E75')))
            fig_avar.update_layout(xaxis_type="log", yaxis_type="log", 
                                  xaxis_title="Tau (s)", yaxis_title="Sigma (Stabilité)",
                                  template="plotly_white", height=500)
            st.plotly_chart(fig_avar, use_container_width=True)
        except: st.error("Données AVAR manquantes.")

else:
    st.info("👋 Prêt pour l'affichage. Veuillez sélectionner un fichier dans l'historique (sidebar) ou en importer un.")

st.sidebar.markdown("---")
st.sidebar.info("PFE 2025/2026 - École Navale")
