import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="SigNoise Cloud Portal", layout="wide", page_icon="📡")

# Custom CSS for better look
st.markdown("""
    <style>
    .main {
        background-color: #F7F7F5;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 SigNoise : Portail de Consultation Cloud")
st.markdown("---")

# Connexion au Google Sheet
try:
    # Utilisation de la connexion native Streamlit pour Google Sheets
    # Nécessite configuration dans .streamlit/secrets.toml
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
except Exception as e:
    st.error(f"Erreur de connexion au Cloud : {e}")
    st.info("Assurez-vous que les secrets Streamlit sont configurés.")
    st.stop()

# Sidebar : Sélection par ID
if not df.empty:
    st.sidebar.header("🔍 Historique Cloud")
    # On trie par date pour avoir les plus récents en premier
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date', ascending=False)
    
    selected_id = st.sidebar.selectbox("Choisir un traitement effectué", df['ID'].unique())

    # Filtrer les données pour l'ID choisi
    row = df[df['ID'] == selected_id].iloc[0]

    # Affichage des indicateurs
    st.subheader(f"Résultats pour l'ID : {selected_id}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date du test", row['Date'].strftime('%d/%m/%Y %H:%M'))
    c2.metric("Émetteur Identifié", row['Decision'])
    c3.metric("Confiance IA", row['Confiance'])
    c4.metric("Source", row['ID'].split('\\')[-1] if '\\' in row['ID'] else row['ID'].split('/')[-1])

    st.markdown("---")

    # Reconstruction des graphiques
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📊 Densité Spectrale (PSD)")
        try:
            x_psd = json.loads(row['PSD_X'])
            y_psd = json.loads(row['PSD_Y'])
            # Shift pour l'affichage comme dans l'app desktop
            x_psd = np.fft.fftshift(x_psd) / 1000 # kHz
            y_psd = np.fft.fftshift(y_psd)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_psd, y=y_psd, mode='lines', line=dict(color='#185FA5')))
            fig.update_layout(
                xaxis_title="Fréquence (kHz)",
                yaxis_title="Puissance (dB)",
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_white",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("Données PSD indisponibles pour ce traitement.")

    with col_right:
        st.markdown("### 📈 Variance d'Allan (AVAR)")
        try:
            ax = json.loads(row['AVAR_X'])
            ay = json.loads(row['AVAR_Y'])
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=ax, y=np.sqrt(ay), mode='lines+markers', line=dict(color='#1D9E75')))
            fig2.update_layout(
                xaxis_type="log",
                yaxis_type="log",
                xaxis_title="Tau (s)",
                yaxis_title="Sigma (Stabilité)",
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_white",
                height=400
            )
            st.plotly_chart(fig2, use_container_width=True)
        except:
            st.warning("Données AVAR indisponibles pour ce traitement.")

    # Section Features
    with st.expander("📝 Détails des Caractéristiques (Features)"):
        st.write("Voici les caractéristiques physiques extraites par l'IA pour ce signal.")
        # On pourrait ajouter plus de colonnes dans le Sheet pour les features
        st.info("Données détaillées disponibles dans le rapport complet.")

else:
    st.warning("Aucune donnée trouvée dans le Google Sheet. Lancez un traitement depuis l'application SigNoise.")

st.sidebar.markdown("---")
st.sidebar.info("PFE 2025/2026 - École Navale")
