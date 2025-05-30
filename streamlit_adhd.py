# -*- coding: utf-8 -*-
"""
Streamlit TDAH - Outil de Dépistage et d'Analyse
Adapté du design moderne du streamlit Autisme
"""

import streamlit as st
import joblib
import prince
import base64
import hashlib
import os
import pickle
import numpy as np
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration de la page
st.set_page_config(
    page_title="Dépistage TDAH",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Création des dossiers de cache
for folder in ['data_cache', 'image_cache', 'model_cache', 'theme_cache']:
    os.makedirs(folder, exist_ok=True)

# État de session pour les scores ADHD-RS
if "adhd_total" not in st.session_state:
    st.session_state.adhd_total = 0

if "adhd_responses" not in st.session_state:
    st.session_state.adhd_responses = []

def initialize_session_state():
    """Initialise l'état de session pour conserver les configurations entre les recharges"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        default_tool = "🏠 Accueil"
        
        try:
            if "selection" in st.query_params:
                selection = st.query_params["selection"]
                selection_mapping = {
                    "📝 Test ADHD-RS": "🤖 Prédiction par IA",
                    "🤖 Prédiction par IA": "🤖 Prédiction par IA",
                    "🔍 Exploration des Données": "🔍 Exploration des Données"
                }
                if selection in selection_mapping:
                    st.session_state.tool_choice = selection_mapping[selection]
                else:
                    st.session_state.tool_choice = default_tool
            else:
                st.session_state.tool_choice = default_tool
        except:
            st.session_state.tool_choice = default_tool

        st.session_state.data_exploration_expanded = True

def set_custom_theme():
    """Définit le thème personnalisé avec palette orange pour le TDAH"""
    css_path = "theme_cache/custom_theme_tdah.css"
    os.makedirs(os.path.dirname(css_path), exist_ok=True)

    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            custom_theme = f.read()
    else:
        custom_theme = """
        <style>
        /* ================ Variables Globales TDAH (Orange) ================ */
        :root {
            --primary: #d84315 !important;
            --secondary: #ff5722 !important;
            --accent: #ff9800 !important;
            --background: #fff8f5 !important;
            --sidebar-bg: #ffffff !important;
            --sidebar-border: #ffccbc !important;
            --text-primary: #d84315 !important;
            --text-secondary: #bf360c !important;
            --sidebar-width-collapsed: 60px !important;
            --sidebar-width-expanded: 240px !important;
            --sidebar-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            --shadow-light: 0 2px 8px rgba(255,87,34,0.08) !important;
            --shadow-medium: 0 4px 16px rgba(255,87,34,0.12) !important;
        }

        /* ================ Structure Principale ================ */
        [data-testid="stAppViewContainer"] {
            background-color: var(--background) !important;
        }

        /* ================ Sidebar Compacte et Professionnelle ================ */
        [data-testid="stSidebar"] {
            width: var(--sidebar-width-collapsed) !important;
            min-width: var(--sidebar-width-collapsed) !important;
            max-width: var(--sidebar-width-collapsed) !important;
            height: 100vh !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            z-index: 999999 !important;
            background: var(--sidebar-bg) !important;
            border-right: 1px solid var(--sidebar-border) !important;
            box-shadow: var(--shadow-light) !important;
            overflow: hidden !important;
            padding: 0 !important;
            transition: var(--sidebar-transition) !important;
        }

        [data-testid="stSidebar"]:hover {
            width: var(--sidebar-width-expanded) !important;
            min-width: var(--sidebar-width-expanded) !important;
            max-width: var(--sidebar-width-expanded) !important;
            box-shadow: var(--shadow-medium) !important;
            overflow-y: auto !important;
        }

        [data-testid="stSidebar"] > div {
            width: var(--sidebar-width-expanded) !important;
            padding: 12px 8px !important;
            height: 100vh !important;
            overflow: hidden !important;
        }

        [data-testid="stSidebar"]:hover > div {
            overflow-y: auto !important;
            padding: 16px 12px !important;
        }

        /* ================ En-tête TDAH ================ */
        [data-testid="stSidebar"] h2 {
            font-size: 0 !important;
            margin: 0 0 20px 0 !important;
            padding: 12px 0 !important;
            border-bottom: 1px solid var(--sidebar-border) !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            height: 60px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        [data-testid="stSidebar"] h2::before {
            content: "🧠" !important;
            font-size: 28px !important;
            display: block !important;
            margin: 0 !important;
        }

        [data-testid="stSidebar"]:hover h2 {
            font-size: 1.4rem !important;
            color: var(--primary) !important;
            font-weight: 600 !important;
        }

        [data-testid="stSidebar"]:hover h2::before {
            font-size: 20px !important;
            margin-right: 8px !important;
        }

        /* ================ Options de Navigation TDAH ================ */
        [data-testid="stSidebar"] .stRadio {
            padding: 0 !important;
            margin: 0 !important;
        }

        [data-testid="stSidebar"] .stRadio > div {
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
            padding: 0 !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            display: flex !important;
            align-items: center !important;
            padding: 10px 6px !important;
            margin: 0 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            position: relative !important;
            height: 44px !important;
            overflow: hidden !important;
            background: transparent !important;
        }

        [data-testid="stSidebar"] .stRadio label > div:first-child {
            display: none !important;
        }

        [data-testid="stSidebar"] .stRadio label span {
            font-size: 0 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            text-align: center !important;
            position: relative !important;
        }

        [data-testid="stSidebar"] .stRadio label span::before {
            font-size: 22px !important;
            display: block !important;
            width: 100% !important;
            text-align: center !important;
        }

        /* Icônes pour le TDAH */
        [data-testid="stSidebar"] .stRadio label:nth-child(1) span::before { content: "🏠" !important; }
        [data-testid="stSidebar"] .stRadio label:nth-child(2) span::before { content: "🔍" !important; }
        [data-testid="stSidebar"] .stRadio label:nth-child(3) span::before { content: "🧠" !important; }
        [data-testid="stSidebar"] .stRadio label:nth-child(4) span::before { content: "🤖" !important; }
        [data-testid="stSidebar"] .stRadio label:nth-child(5) span::before { content: "📚" !important; }
        [data-testid="stSidebar"] .stRadio label:nth-child(6) span::before { content: "ℹ️" !important; }

        [data-testid="stSidebar"]:hover .stRadio label span {
            font-size: 14px !important;
            font-weight: 500 !important;
            text-align: left !important;
            padding-left: 12px !important;
        }

        [data-testid="stSidebar"]:hover .stRadio label span::before {
            font-size: 18px !important;
            position: absolute !important;
            left: -8px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: auto !important;
        }

        /* Effets de survol orange */
        [data-testid="stSidebar"] .stRadio label:hover {
            background: linear-gradient(135deg, #fff3e0, #ffe0b2) !important;
            transform: translateX(3px) !important;
            box-shadow: var(--shadow-light) !important;
        }

        [data-testid="stSidebar"] .stRadio label[data-checked="true"] {
            background: linear-gradient(135deg, var(--secondary), var(--accent)) !important;
            color: white !important;
            box-shadow: var(--shadow-medium) !important;
        }

        [data-testid="stSidebar"] .stRadio label[data-checked="true"]:hover {
            background: linear-gradient(135deg, var(--accent), var(--secondary)) !important;
            transform: translateX(5px) !important;
        }

        /* ================ Contenu Principal Adaptatif ================ */
        .main .block-container {
            margin-left: calc(var(--sidebar-width-collapsed) + 16px) !important;
            padding: 1.5rem !important;
            max-width: calc(100vw - var(--sidebar-width-collapsed) - 32px) !important;
            transition: var(--sidebar-transition) !important;
        }

        /* ================ Boutons TDAH ================ */
        .stButton > button {
            background: linear-gradient(135deg, var(--secondary), var(--accent)) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 10px 20px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
            box-shadow: var(--shadow-light) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-medium) !important;
            background: linear-gradient(135deg, var(--accent), var(--secondary)) !important;
        }

        /* Styles pour les cartes modernes */
        .info-card-modern {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(255,87,34,0.08);
            border-left: 4px solid var(--secondary);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .info-card-modern:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(255,87,34,0.15);
        }

        /* Suppression des alertes indésirables */
        .stAlert, [data-testid="stAlert"] {
            border: none !important;
            background: transparent !important;
        }
        </style>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            
            if (sidebar) {
                let isExpanded = false;
                let hoverTimeout;
                
                function expandSidebar() {
                    clearTimeout(hoverTimeout);
                    isExpanded = true;
                    sidebar.style.overflow = 'visible';
                }
                
                function collapseSidebar() {
                    hoverTimeout = setTimeout(() => {
                        isExpanded = false;
                        sidebar.style.overflow = 'hidden';
                    }, 200);
                }
                
                sidebar.addEventListener('mouseenter', expandSidebar);
                sidebar.addEventListener('mouseleave', collapseSidebar);
                
                // Attribution des états pour les options sélectionnées
                const observer = new MutationObserver(() => {
                    const radioLabels = sidebar.querySelectorAll('.stRadio label');
                    radioLabels.forEach(label => {
                        const input = label.querySelector('input[type="radio"]');
                        if (input && input.checked) {
                            label.setAttribute('data-checked', 'true');
                        } else {
                            label.setAttribute('data-checked', 'false');
                        }
                    });
                });
                
                observer.observe(sidebar, { 
                    childList: true, 
                    subtree: true,
                    attributes: true 
                });
            }
        });
        </script>
        """
        
        with open(css_path, 'w') as f:
            f.write(custom_theme)

    st.markdown(custom_theme, unsafe_allow_html=True)

def show_navigation_menu():
    """Menu de navigation optimisé pour le TDAH"""
    st.markdown("## 🧠 TDAH - Navigation")
    st.markdown("Choisissez un outil :")

    options = [
        "🏠 Accueil",
        "🔍 Exploration", 
        "🧠 Analyse ML",
        "🤖 Prédiction par IA",
        "📚 Documentation",
        "ℹ️ À propos"
    ]

    if 'tool_choice' not in st.session_state or st.session_state.tool_choice not in options:
        st.session_state.tool_choice = "🏠 Accueil"

    current_index = options.index(st.session_state.tool_choice)

    tool_choice = st.radio(
        "",
        options,
        label_visibility="collapsed",
        index=current_index,
        key="main_navigation"
    )

    if tool_choice != st.session_state.tool_choice:
        st.session_state.tool_choice = tool_choice

    return tool_choice

@st.cache_data(ttl=86400)
def get_img_with_href(img_url, target_url, as_banner=False):
    """Crée une image cliquable avec un lien"""
    if "drive.google.com" in img_url and "/d/" in img_url:
        file_id = img_url.split("/d/")[1].split("/")[0]
        img_url = f"https://drive.google.com/uc?export=view&id={file_id}"

    cache_filename = hashlib.md5(img_url.encode()).hexdigest() + ".webp"
    cache_dir = "image_cache"
    cache_path = os.path.join(cache_dir, cache_filename)
    os.makedirs(cache_dir, exist_ok=True)

    try:
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                img_data = f.read()
            img = Image.open(BytesIO(img_data))
        else:
            response = requests.get(img_url, timeout=15)
            response.raise_for_status()

            if len(response.content) == 0:
                raise Exception("Contenu vide téléchargé")

            img = Image.open(BytesIO(response.content))

            max_width = 1200 if as_banner else 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=85, optimize=True)

            with open(cache_path, "wb") as f:
                f.write(buffer.getvalue())

            buffer.seek(0)
            img_data = buffer.getvalue()

        img_str = base64.b64encode(img_data).decode()

        if as_banner:
            style = 'style="width:100%;height:600px;display:block;object-fit:cover;border-radius:10px;" loading="lazy"'
        else:
            style = 'style="width:100%;height:auto;display:block;object-fit:contain;margin:0 auto;padding:0;" loading="lazy"'

        container_style = 'style="width:100%; padding:10px; background-color:white; border-radius:10px; overflow:hidden; margin-bottom:20px;"'

        if target_url and target_url != "#":
            html_code = f'<div {container_style}><a href="{target_url}" target="_blank" style="display:block; margin:0; padding:0; line-height:0;"><img src="data:image/webp;base64,{img_str}" {style}></a></div>'
        else:
            html_code = f'<div {container_style}><img src="data:image/webp;base64,{img_str}" {style}></div>'

        return html_code
    except Exception as e:
        return f'<div style="text-align:center;padding:20px;background:#f0f2f6;border-radius:10px;"><p>Image non disponible ({str(e)})</p></div>'

@st.cache_data(ttl=86400)
def load_dataset():
    """Charge les datasets TDAH - Version simulée pour l'exemple"""
    try:
        # Simulation de données TDAH pour l'exemple
        # Dans un vrai cas, vous chargeriez vos vraies données
        np.random.seed(42)
        n_samples = 1500
        
        # Génération de données simulées pour le TDAH
        df = pd.DataFrame({
            'Age': np.random.normal(35, 12, n_samples).astype(int),
            'Genre': np.random.choice(['M', 'F'], n_samples, p=[0.6, 0.4]),
            'Education': np.random.choice(['Primaire', 'Secondaire', 'Supérieur'], n_samples),
            'Hyperactivite_Score': np.random.randint(0, 28, n_samples),
            'Inattention_Score': np.random.randint(0, 28, n_samples),
            'Impulsivite_Score': np.random.randint(0, 20, n_samples),
            'Troubles_Apprentissage': np.random.choice(['Oui', 'Non'], n_samples, p=[0.3, 0.7]),
            'Antecedents_Familiaux': np.random.choice(['Oui', 'Non'], n_samples, p=[0.4, 0.6]),
            'Statut_testeur': np.random.choice(['Famille', 'Medecin', 'Psychologue', 'Auto'], n_samples),
        })
        
        # Génération du score total ADHD-RS (18 items, 0-3 chaque)
        for i in range(1, 19):
            df[f'Q{i}'] = np.random.randint(0, 4, n_samples)
        
        df['Score_ADHD_Total'] = df[[f'Q{i}' for i in range(1, 19)]].sum(axis=1)
        
        # Génération de la variable cible TDAH basée sur les scores
        tdah_prob = (df['Score_ADHD_Total'] / 54) * 0.8 + 0.1  # Probabilité basée sur le score
        df['TDAH'] = np.random.binomial(1, tdah_prob, n_samples)
        df['TDAH'] = df['TDAH'].map({1: 'Oui', 0: 'Non'})
        
        # Nettoyage des âges aberrants
        df.loc[df['Age'] < 6, 'Age'] = np.random.randint(6, 18, (df['Age'] < 6).sum())
        df.loc[df['Age'] > 65, 'Age'] = np.random.randint(18, 65, (df['Age'] > 65).sum())
        
        # Datasets simulés pour compatibilité
        df_ds1 = df.sample(300, random_state=1).copy()
        df_ds2 = df.sample(400, random_state=2).copy()
        df_ds3 = df.sample(350, random_state=3).copy()
        df_ds4 = df.sample(250, random_state=4).copy()
        df_ds5 = df.sample(200, random_state=5).copy()
        
        df_stats = {
            'mean_by_tdah': df.groupby('TDAH').mean(numeric_only=True),
            'count_by_tdah': df.groupby('TDAH').count(),
            'categorical_cols': df.select_dtypes(include=['object']).columns.tolist(),
            'numeric_cols': df.select_dtypes(exclude=['object']).columns.tolist()
        }

        return df, df_ds1, df_ds2, df_ds3, df_ds4, df_ds5, df_stats
    except Exception as e:
        st.error(f"Erreur lors du chargement: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def show_home_page():
    """Page d'accueil pour le TDAH avec design moderne"""
    
    # CSS spécifique pour la page d'accueil
    st.markdown("""
    <style>
    .info-card-modern {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(255,87,34,0.08);
        border-left: 4px solid #ff5722;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .info-card-modern:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(255,87,34,0.15);
    }
    
    .timeline-container {
        background-color: #fff3e0;
        padding: 25px;
        border-radius: 15px;
        margin: 25px 0;
        overflow-x: auto;
    }
    
    .timeline-item {
        min-width: 160px;
        text-align: center;
        margin: 0 15px;
        flex-shrink: 0;
    }
    
    .timeline-year {
        background: linear-gradient(135deg, #ff5722, #ff9800);
        color: white;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.95rem;
    }
    
    .timeline-text {
        margin-top: 12px;
        font-size: 0.9rem;
        color: #d84315;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    # En-tête principal
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            🧠 Comprendre le Trouble Déficitaire de l'Attention avec Hyperactivité
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Une approche moderne et scientifique pour le dépistage précoce du TDAH
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section "Qu'est-ce que le TDAH ?"
    st.markdown("""
    <div class="info-card-modern">
        <h2 style="color: #ff5722; margin-bottom: 25px; font-size: 2.2rem; text-align: center;">
            🔬 Qu'est-ce que le TDAH ?
        </h2>
        <p style="font-size: 1.2rem; line-height: 1.8; text-align: justify;
                  max-width: 900px; margin: 0 auto; color: #d84315;">
            Le <strong>Trouble Déficitaire de l'Attention avec ou sans Hyperactivité (TDAH)</strong> est un trouble
            neurodéveloppemental qui se caractérise par des difficultés persistantes d'attention, d'hyperactivité
            et d'impulsivité. Ces symptômes apparaissent avant l'âge de 12 ans et interfèrent significativement
            avec le fonctionnement quotidien dans plusieurs domaines de la vie.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Timeline de l'évolution
    st.markdown("""
    <h2 style="color: #ff5722; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        📅 Évolution de la compréhension du TDAH
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="timeline-container">
        <div style="display: flex; justify-content: space-between; min-width: 700px;">
            <div class="timeline-item">
                <div class="timeline-year">1902</div>
                <div class="timeline-text">Still décrit l'hyperactivité chez l'enfant</div>
            </div>
            <div class="timeline-item">
                <div class="timeline-year">1980</div>
                <div class="timeline-text">Le TDAH entre dans le DSM-III</div>
            </div>
            <div class="timeline-item">
                <div class="timeline-year">1994</div>
                <div class="timeline-text">Définition des 3 sous-types</div>
            </div>
            <div class="timeline-item">
                <div class="timeline-year">Aujourd'hui</div>
                <div class="timeline-text">Approche neuroscientifique</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section "Les trois dimensions du TDAH"
    st.markdown("## 🌈 Les trois dimensions du TDAH")

    st.markdown("""
    <div style="background-color: white; padding: 25px; border-radius: 15px;
               box-shadow: 0 4px 15px rgba(255,87,34,0.08); border-left: 4px solid #ff5722;">
        <p style="font-size: 1.1rem; line-height: 1.7; color: #d84315; margin-bottom: 20px;">
            Le TDAH se manifeste selon <strong>trois dimensions principales</strong> qui peuvent se présenter
            séparément ou en combinaison.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Les trois types
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffebee, #ffcdd2);
                   border-radius: 15px; padding: 25px; margin-bottom: 20px; height: 200px;
                   border-left: 4px solid #f44336;">
            <h4 style="color: #c62828; margin-top: 0;">🎯 Inattention</h4>
            <ul style="color: #d32f2f; line-height: 1.6; font-size: 0.9rem;">
                <li>Difficultés de concentration</li>
                <li>Oublis fréquents</li>
                <li>Désorganisation</li>
                <li>Évitement des tâches</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fff3e0, #ffcc02);
                   border-radius: 15px; padding: 25px; margin-bottom: 20px; height: 200px;
                   border-left: 4px solid #ff9800;">
            <h4 style="color: #ef6c00; margin-top: 0;">⚡ Hyperactivité</h4>
            <ul style="color: #f57c00; line-height: 1.6; font-size: 0.9rem;">
                <li>Agitation constante</li>
                <li>Difficulté à rester assis</li>
                <li>Énergie excessive</li>
                <li>Verbosité</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e8f5e8, #c8e6c9);
                   border-radius: 15px; padding: 25px; margin-bottom: 20px; height: 200px;
                   border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-top: 0;">🚀 Impulsivité</h4>
            <ul style="color: #388e3c; line-height: 1.6; font-size: 0.9rem;">
                <li>Réponses précipitées</li>
                <li>Interruptions fréquentes</li>
                <li>Impatience</li>
                <li>Prises de risques</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Section prévalence
    st.subheader("📈 Prévalence du TDAH")

    st.info("""
    **Données clés sur le TDAH :**

    • **5-7%** des enfants d'âge scolaire sont concernés
    • **2.5%** des adultes vivent avec un TDAH
    • Ratio garçons/filles d'environ **3:1** chez l'enfant
    • **Persistance à l'âge adulte** dans 60% des cas
    """)

    # Section "À qui s'adresse ce projet"
    st.markdown("""
    <h2 style="color: #ff5722; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        🎯 À qui s'adresse ce projet
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 10, 1])

    with col2:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fff3e0, #ffcc02);
                       border-radius: 15px; padding: 25px; margin-bottom: 20px; height: 180px;
                       border-left: 4px solid #ff9800;">
                <h4 style="color: #ef6c00; margin-top: 0;">🔬 Professionnels de santé</h4>
                <p style="color: #f57c00; line-height: 1.6; font-size: 0.95rem;">
                    Outil d'aide au diagnostic et d'évaluation des symptômes TDAH
                    pour améliorer la prise en charge.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: linear-gradient(135deg, #ffebee, #ffcdd2);
                       border-radius: 15px; padding: 25px; height: 180px;
                       border-left: 4px solid #f44336;">
                <h4 style="color: #c62828; margin-top: 0;">👨‍👩‍👧‍👦 Familles et particuliers</h4>
                <p style="color: #d32f2f; line-height: 1.6; font-size: 0.95rem;">
                    Outils d'auto-évaluation et d'information pour identifier
                    les signes précoces du TDAH.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #e8f5e8, #c8e6c9);
                       border-radius: 15px; padding: 25px; margin-bottom: 20px; height: 180px;
                       border-left: 4px solid #4caf50;">
                <h4 style="color: #2e7d32; margin-top: 0;">🎓 Milieu éducatif</h4>
                <p style="color: #388e3c; line-height: 1.6; font-size: 0.95rem;">
                    Ressources pour enseignants et éducateurs pour mieux
                    comprendre et accompagner les élèves avec TDAH.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                       border-radius: 15px; padding: 25px; height: 180px;
                       border-left: 4px solid #2196f3;">
                <h4 style="color: #1565c0; margin-top: 0;">🏛️ Recherche et politique</h4>
                <p style="color: #1976d2; line-height: 1.6; font-size: 0.95rem;">
                    Données et analyses pour orienter les politiques de santé
                    publique et les recherches futures.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Section "Caractéristiques principales"
    st.markdown("""
    <h2 style="color: #ff5722; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        🧠 Impact du TDAH
    </h2>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card-modern" style="border-left-color: #ff5722;">
            <h3 style="color: #ff5722; margin-bottom: 20px;">🎓 Domaine scolaire/professionnel</h3>
            <ul style="line-height: 1.8; color: #d84315; padding-left: 20px;">
                <li>Difficultés de concentration en classe</li>
                <li>Problèmes d'organisation</li>
                <li>Procrastination</li>
                <li>Sous-performance académique</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card-modern" style="border-left-color: #ff9800;">
            <h3 style="color: #ff9800; margin-bottom: 20px;">👥 Relations sociales</h3>
            <ul style="line-height: 1.8; color: #ef6c00; padding-left: 20px;">
                <li>Difficultés dans les interactions</li>
                <li>Problèmes de régulation émotionnelle</li>
                <li>Impulsivité relationnelle</li>
                <li>Estime de soi fragile</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Section "Notre approche" finale
    st.markdown("""
    <h2 style="color: #ff5722; margin: 45px 0 25px 0; text-align: center; font-size: 2.2rem;">
        🚀 Notre approche
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 10, 1])

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                   padding: 35px; border-radius: 20px; text-align: center; color: white;
                   box-shadow: 0 8px 25px rgba(255, 87, 34, 0.3);">
            <p style="font-size: 1.3rem; max-width: 800px; margin: 0 auto; line-height: 1.7;">
                Notre plateforme combine l'expertise clinique et l'intelligence artificielle
                pour améliorer le dépistage précoce du TDAH et optimiser l'accompagnement
                des personnes concernées dans une approche bienveillante et scientifique.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Avertissement final
    st.markdown("""
    <div style="margin: 40px 0 30px 0; padding: 20px; border-radius: 12px;
               border-left: 4px solid #f44336; background: linear-gradient(135deg, #ffebee, #ffcdd2);
               box-shadow: 0 4px 12px rgba(244, 67, 54, 0.1);">
        <p style="font-size: 1rem; color: #c62828; text-align: center; margin: 0; line-height: 1.6;">
            <strong style="color: #f44336;">⚠️ Avertissement :</strong>
            Les informations présentées sur cette plateforme sont à titre informatif uniquement.
            Elles ne remplacent pas l'avis médical professionnel pour le diagnostic du TDAH.
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_data_exploration():
    """Exploration des données TDAH avec visualisations interactives"""
    df, df_ds1, df_ds2, df_ds3, df_ds4, df_ds5, df_stats = load_dataset()
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            🔍 Exploration des Données TDAH
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Analyse approfondie des patterns et caractéristiques du TDAH
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Structure des données
    with st.expander("📂 Structure des Données", expanded=True):
        st.markdown("""
        <div style="background:#fff3e0; padding:15px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.05)">
            <h4 style="color:#e65100; border-bottom:1px solid #ffcc02; padding-bottom:8px">Jeux de Données TDAH</h4>
            <ul style="padding-left:20px">
                <li>📁 <strong>Dataset Principal:</strong> Données synthétiques TDAH (n=1500)</li>
                <li>📁 <strong>Variables cliniques:</strong> Scores ADHD-RS, démographie</li>
                <li>📁 <strong>Évaluations:</strong> 18 items du questionnaire ADHD-RS</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        tab_main, tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Dataset Principal", "Sous-échantillon 1", "Sous-échantillon 2", 
            "Sous-échantillon 3", "Sous-échantillon 4", "Sous-échantillon 5"
        ])

        with tab_main:
            st.caption("Dataset Principal TDAH")
            st.dataframe(df.head(10), use_container_width=True)
        with tab1:
            st.dataframe(df_ds1.head(5), use_container_width=True)
        with tab2:
            st.dataframe(df_ds2.head(5), use_container_width=True)
        with tab3:
            st.dataframe(df_ds3.head(5), use_container_width=True)
        with tab4:
            st.dataframe(df_ds4.head(5), use_container_width=True)
        with tab5:
            st.dataframe(df_ds5.head(5), use_container_width=True)

    # Statistiques descriptives
    with st.expander("📈 Statistiques Descriptives", expanded=True):
        st.subheader("Vue d'ensemble du dataset")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Participants", len(df), "Total échantillon")
        with col2:
            tdah_count = (df['TDAH'] == 'Oui').sum()
            st.metric("Cas TDAH", tdah_count, f"{tdah_count/len(df):.1%}")
        with col3:
            age_mean = df['Age'].mean()
            st.metric("Âge moyen", f"{age_mean:.1f} ans", f"±{df['Age'].std():.1f}")
        with col4:
            male_ratio = (df['Genre'] == 'M').mean()
            st.metric("Ratio H/F", f"{male_ratio:.1%}", "Hommes")

        # Distributions par variables
        st.subheader("Distributions des variables clés")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution âge
            fig_age = px.histogram(df, x='Age', color='TDAH', 
                                 title="Distribution de l'âge par diagnostic TDAH",
                                 color_discrete_map={'Oui': '#ff5722', 'Non': '#ff9800'})
            st.plotly_chart(fig_age, use_container_width=True)
            
        with col2:
            # Distribution score total
            fig_score = px.box(df, x='TDAH', y='Score_ADHD_Total',
                             title="Distribution des scores ADHD-RS",
                             color='TDAH',
                             color_discrete_map={'Oui': '#ff5722', 'Non': '#ff9800'})
            st.plotly_chart(fig_score, use_container_width=True)

    # Analyse des corrélations
    with st.expander("🔗 Analyse des Corrélations", expanded=True):
        st.subheader("Matrice de corrélation des variables numériques")
        
        # Sélection des variables numériques pertinentes
        numeric_cols = ['Age', 'Hyperactivite_Score', 'Inattention_Score', 'Impulsivite_Score', 'Score_ADHD_Total']
        corr_matrix = df[numeric_cols].corr()
        
        fig_corr = px.imshow(corr_matrix, 
                           title="Corrélations entre les scores TDAH",
                           color_continuous_scale='RdBu_r',
                           aspect="auto")
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Top corrélations
        st.subheader("Corrélations les plus fortes")
        
        # Extraire les corrélations sans la diagonale
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_pairs.append({
                    'Variable 1': corr_matrix.columns[i],
                    'Variable 2': corr_matrix.columns[j],
                    'Corrélation': corr_matrix.iloc[i, j]
                })
        
        corr_df = pd.DataFrame(corr_pairs).sort_values('Corrélation', key=abs, ascending=False)
        st.dataframe(corr_df.head(10), use_container_width=True)

    # Analyse par questionnaire
    with st.expander("📝 Analyse du Questionnaire ADHD-RS", expanded=True):
        st.subheader("Analyse des réponses aux 18 items ADHD-RS")
        
        # Analyse des réponses par item
        question_cols = [f'Q{i}' for i in range(1, 19)]
        
        # Moyennes par diagnostic
        item_means = df.groupby('TDAH')[question_cols].mean()
        
        fig_items = go.Figure()
        
        fig_items.add_trace(go.Bar(
            name='TDAH Positif',
            x=question_cols,
            y=item_means.loc['Oui'],
            marker_color='#ff5722'
        ))
        
        fig_items.add_trace(go.Bar(
            name='TDAH Négatif', 
            x=question_cols,
            y=item_means.loc['Non'],
            marker_color='#ff9800'
        ))
        
        fig_items.update_layout(
            title="Scores moyens par item du questionnaire ADHD-RS",
            xaxis_title="Items du questionnaire",
            yaxis_title="Score moyen (0-3)",
            barmode='group'
        )
        
        st.plotly_chart(fig_items, use_container_width=True)
        
        # Distribution des scores totaux
        st.subheader("Distribution des scores totaux ADHD-RS")
        
        fig_dist = px.histogram(df, x='Score_ADHD_Total', color='TDAH',
                              title="Distribution des scores totaux ADHD-RS",
                              nbins=30,
                              color_discrete_map={'Oui': '#ff5722', 'Non': '#ff9800'})
        st.plotly_chart(fig_dist, use_container_width=True)

def load_ml_libraries():
    """Charge les bibliothèques ML nécessaires"""
    global RandomForestClassifier, LogisticRegression, StandardScaler, OneHotEncoder
    global ColumnTransformer, Pipeline, accuracy_score, precision_score, recall_score
    global f1_score, roc_auc_score, confusion_matrix, classification_report
    global cross_val_score, train_test_split, roc_curve, precision_recall_curve
    
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                                f1_score, roc_auc_score, confusion_matrix, 
                                classification_report, roc_curve, precision_recall_curve)
    from sklearn.model_selection import cross_val_score, train_test_split

@st.cache_resource
def train_tdah_model(df):
    """Entraîne un modèle pour prédire le TDAH"""
    load_ml_libraries()
    
    try:
        if 'TDAH' not in df.columns:
            st.error("La colonne 'TDAH' n'existe pas dans le dataframe")
            return None, None, None

        # Préparation des données
        X = df.drop(columns=['TDAH'])
        y = df['TDAH'].map({'Oui': 1, 'Non': 0})

        # Identification des colonnes numériques et catégorielles
        numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

        # Préprocesseur
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_cols),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
            ],
            remainder='passthrough',
            verbose_feature_names_out=False
        )

        # Modèle Random Forest
        rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1
        )

        # Pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', rf_classifier)
        ])

        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Entraînement
        pipeline.fit(X_train, y_train)

        # Feature names
        try:
            feature_names = preprocessor.get_feature_names_out()
        except:
            feature_names = [f"feature_{i}" for i in range(len(pipeline.named_steps['classifier'].feature_importances_))]

        return pipeline, preprocessor, feature_names, X_test, y_test

    except Exception as e:
        st.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
        return None, None, None, None, None

def show_ml_analysis():
    """Analyse ML pour le TDAH avec visualisations"""
    load_ml_libraries()
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            🧠 Analyse Machine Learning - TDAH
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Modèles prédictifs pour l'aide au diagnostic du TDAH
        </p>
    </div>
    """, unsafe_allow_html=True)

    df, _, _, _, _, _, _ = load_dataset()
    
    # Onglets ML
    ml_tabs = st.tabs([
        "📊 Préparation des données",
        "🚀 Entraînement du modèle", 
        "📈 Performance du modèle",
        "🎯 Prédictions"
    ])

    with ml_tabs[0]:
        st.subheader("📊 Préparation des données pour le ML")
        
        # Informations sur le dataset
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Échantillons totaux", len(df))
        with col2:
            tdah_positive = (df['TDAH'] == 'Oui').sum()
            st.metric("Cas TDAH positifs", tdah_positive, f"{tdah_positive/len(df):.1%}")
        with col3:
            features_count = len(df.columns) - 1  # -1 pour exclure la variable cible
            st.metric("Variables prédictives", features_count)

        # Distribution de la variable cible
        st.subheader("Distribution de la variable cible")
        
        fig_target = px.pie(df, names='TDAH', 
                          title="Répartition des diagnostics TDAH",
                          color_discrete_map={'Oui': '#ff5722', 'Non': '#ff9800'})
        st.plotly_chart(fig_target, use_container_width=True)

        # Aperçu des variables
        st.subheader("Aperçu des variables prédictives")
        
        # Variables numériques
        numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if 'TDAH' in numerical_cols:
            numerical_cols.remove('TDAH')
            
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if 'TDAH' in categorical_cols:
            categorical_cols.remove('TDAH')

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Variables numériques:**")
            for col in numerical_cols[:10]:  # Limiter l'affichage
                st.write(f"• {col}")
            if len(numerical_cols) > 10:
                st.write(f"... et {len(numerical_cols) - 10} autres")
                
        with col2:
            st.markdown("**Variables catégorielles:**")
            for col in categorical_cols:
                st.write(f"• {col}")

    with ml_tabs[1]:
        st.subheader("🚀 Entraînement du modèle Random Forest")
        
        with st.spinner("Entraînement du modèle en cours..."):
            model_results = train_tdah_model(df)
            
        if model_results[0] is not None:
            pipeline, preprocessor, feature_names, X_test, y_test = model_results
            
            st.success("✅ Modèle entraîné avec succès!")
            
            # Informations sur l'entraînement
            st.subheader("Configuration du modèle")
            
            model_config = {
                "Algorithme": "Random Forest",
                "Nombre d'arbres": 100,
                "Profondeur max": 8,
                "Échantillons min pour split": 10,
                "Échantillons min par feuille": 2,
                "Features par split": "sqrt"
            }
            
            config_df = pd.DataFrame(list(model_config.items()), columns=['Paramètre', 'Valeur'])
            st.dataframe(config_df, use_container_width=True)
            
        else:
            st.error("❌ Échec de l'entraînement du modèle")

    with ml_tabs[2]:
        if 'pipeline' in locals() and pipeline is not None:
            st.subheader("📈 Évaluation de la performance")
            
            # Prédictions
            y_pred = pipeline.predict(X_test)
            y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
            
            # Métriques
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_test, y_pred_proba)
            
            # Affichage des métriques
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Accuracy", f"{accuracy:.3f}")
            with col2:
                st.metric("Precision", f"{precision:.3f}")
            with col3:
                st.metric("Recall", f"{recall:.3f}")
            with col4:
                st.metric("F1-Score", f"{f1:.3f}")
            with col5:
                st.metric("AUC-ROC", f"{auc:.3f}")
            
            # Matrice de confusion
            st.subheader("Matrice de confusion")
            
            cm = confusion_matrix(y_test, y_pred)
            
            fig_cm = px.imshow(cm, 
                             text_auto=True,
                             aspect="auto",
                             title="Matrice de confusion",
                             labels=dict(x="Prédiction", y="Réalité"),
                             x=['Non-TDAH', 'TDAH'],
                             y=['Non-TDAH', 'TDAH'])
            st.plotly_chart(fig_cm, use_container_width=True)
            
            # Courbe ROC
            st.subheader("Courbe ROC")
            
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
            
            fig_roc = go.Figure()
            fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', 
                                       name=f'ROC (AUC = {auc:.3f})',
                                       line=dict(color='#ff5722', width=3)))
            fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
                                       name='Baseline', 
                                       line=dict(dash='dash', color='gray')))
            fig_roc.update_layout(
                title='Courbe ROC',
                xaxis_title='Taux de Faux Positifs',
                yaxis_title='Taux de Vrais Positifs'
            )
            st.plotly_chart(fig_roc, use_container_width=True)
            
            # Importance des variables
            st.subheader("Importance des variables")
            
            importances = pipeline.named_steps['classifier'].feature_importances_
            importance_df = pd.DataFrame({
                'Variable': feature_names,
                'Importance': importances
            }).sort_values('Importance', ascending=False).head(15)
            
            fig_importance = px.bar(importance_df, x='Importance', y='Variable',
                                  orientation='h',
                                  title="Top 15 des variables les plus importantes",
                                  color='Importance',
                                  color_continuous_scale='Oranges')
            st.plotly_chart(fig_importance, use_container_width=True)
            
        else:
            st.warning("Veuillez d'abord entraîner le modèle dans l'onglet précédent.")

    with ml_tabs[3]:
        if 'pipeline' in locals() and pipeline is not None:
            st.subheader("🎯 Outil de prédiction TDAH")
            
            st.markdown("""
            <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #ff9800;">
                <h4 style="color: #ef6c00; margin-top: 0;">Prédiction basée sur les variables du modèle</h4>
                <p style="color: #f57c00;">Entrez les valeurs pour obtenir une estimation du risque TDAH.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Interface de prédiction
            col1, col2 = st.columns(2)
            
            with col1:
                age_input = st.slider("Âge", min_value=6, max_value=65, value=25)
                genre_input = st.selectbox("Genre", options=['M', 'F'])
                education_input = st.selectbox("Niveau d'éducation", 
                                             options=['Primaire', 'Secondaire', 'Supérieur'])
                troubles_input = st.selectbox("Troubles d'apprentissage", options=['Oui', 'Non'])
                
            with col2:
                hyperactivite_input = st.slider("Score Hyperactivité", min_value=0, max_value=27, value=10)
                inattention_input = st.slider("Score Inattention", min_value=0, max_value=27, value=10)
                impulsivite_input = st.slider("Score Impulsivité", min_value=0, max_value=20, value=8)
                antecedents_input = st.selectbox("Antécédents familiaux", options=['Oui', 'Non'])
                
            # Calcul du score total (simulation des questions Q1-Q18)
            score_total = hyperactivite_input + inattention_input + impulsivite_input
            
            # Bouton de prédiction
            if st.button("🔮 Prédire le risque TDAH", key="predict_tdah"):
                # Créer le DataFrame d'input
                input_data = pd.DataFrame({
                    'Age': [age_input],
                    'Genre': [genre_input],
                    'Education': [education_input],
                    'Hyperactivite_Score': [hyperactivite_input],
                    'Inattention_Score': [inattention_input],
                    'Impulsivite_Score': [impulsivite_input],
                    'Troubles_Apprentissage': [troubles_input],
                    'Antecedents_Familiaux': [antecedents_input],
                    'Statut_testeur': ['Auto'],  # Valeur par défaut
                    'Score_ADHD_Total': [score_total]
                })
                
                # Ajouter les questions Q1-Q18 avec des valeurs simulées
                for i in range(1, 19):
                    input_data[f'Q{i}'] = [np.random.randint(0, 4)]  # Simulation
                
                try:
                    # Prédiction
                    prediction = pipeline.predict(input_data)[0]
                    probability = pipeline.predict_proba(input_data)[0, 1]
                    
                    # Affichage du résultat
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if prediction == 1:
                            st.error(f"⚠️ Risque TDAH détecté")
                        else:
                            st.success(f"✅ Risque TDAH faible")
                    
                    with col2:
                        st.metric("Probabilité TDAH", f"{probability:.1%}")
                        
                    with col3:
                        if probability > 0.7:
                            st.error("Risque élevé")
                        elif probability > 0.3:
                            st.warning("Risque modéré")
                        else:
                            st.success("Risque faible")
                    
                    # Interprétation
                    st.subheader("💡 Interprétation")
                    
                    if probability > 0.7:
                        st.markdown("""
                        <div style="background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #f44336;">
                            <strong>Recommandation :</strong> Les scores suggèrent un risque élevé de TDAH. 
                            Une évaluation clinique approfondie par un professionnel de santé est fortement recommandée.
                        </div>
                        """, unsafe_allow_html=True)
                    elif probability > 0.3:
                        st.markdown("""
                        <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
                            <strong>Recommandation :</strong> Les scores indiquent un risque modéré. 
                            Il pourrait être utile de consulter un professionnel pour une évaluation plus poussée.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                            <strong>Recommandation :</strong> Les scores suggèrent un risque faible de TDAH. 
                            Continuez à surveiller les symptômes si des préoccupations persistent.
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Erreur lors de la prédiction : {str(e)}")
                    
        else:
            st.warning("Veuillez d'abord entraîner le modèle dans les onglets précédents.")

def show_ai_prediction():
    """Interface de prédiction IA pour le TDAH"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            🤖 Prédiction IA - Dépistage TDAH
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Outil d'aide au dépistage précoce du TDAH
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; margin-bottom: 30px; border-left: 4px solid #ff9800;">
        <h3 style="color: #ef6c00; margin-top: 0;">🎯 Objectif de l'outil</h3>
        <p style="color: #f57c00; line-height: 1.6;">
            Cet outil utilise l'intelligence artificielle pour analyser les réponses et fournir une estimation
            du risque de TDAH. Il s'agit d'un outil d'aide au dépistage qui ne remplace pas un diagnostic médical.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Interface de saisie simplifiée
    st.subheader("📝 Questionnaire de dépistage rapide")
    
    with st.form("tdah_screening_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Informations générales**")
            age = st.number_input("Âge", min_value=6, max_value=65, value=25)
            gender = st.selectbox("Genre", ["Masculin", "Féminin"])
            education = st.selectbox("Niveau d'éducation", 
                                   ["Primaire", "Secondaire", "Supérieur"])
            
            st.markdown("**Symptômes d'inattention (0-3)**")
            q1 = st.slider("Difficulté à maintenir l'attention", 0, 3, 1)
            q2 = st.slider("Oublis dans les activités quotidiennes", 0, 3, 1)
            q3 = st.slider("Difficulté à organiser les tâches", 0, 3, 1)
            q4 = st.slider("Évite les tâches nécessitant un effort mental", 0, 3, 1)
            q5 = st.slider("Perd souvent des objets", 0, 3, 1)
            
        with col2:
            st.markdown("**Antécédents**")
            family_history = st.selectbox("Antécédents familiaux de TDAH", ["Oui", "Non", "Ne sait pas"])
            learning_difficulties = st.selectbox("Difficultés d'apprentissage", ["Oui", "Non"])
            
            st.markdown("**Symptômes d'hyperactivité/impulsivité (0-3)**")
            q6 = st.slider("Agitation des mains/pieds", 0, 3, 1)
            q7 = st.slider("Difficulté à rester assis", 0, 3, 1)
            q8 = st.slider("Parle excessivement", 0, 3, 1)
            q9 = st.slider("Répond avant la fin des questions", 0, 3, 1)
            q10 = st.slider("Difficulté à attendre son tour", 0, 3, 1)
        
        submitted = st.form_submit_button("🔮 Analyser le risque TDAH", use_container_width=True)
        
        if submitted:
            # Calcul des scores
            inattention_score = q1 + q2 + q3 + q4 + q5
            hyperactivite_score = q6 + q7 + q8 + q9 + q10
            total_score = inattention_score + hyperactivite_score
            
            # Simulation d'une prédiction IA
            # Dans un vrai cas, vous utiliseriez votre modèle entraîné
            risk_factors = 0
            
            if total_score > 20:
                risk_factors += 3
            elif total_score > 15:
                risk_factors += 2
            elif total_score > 10:
                risk_factors += 1
                
            if family_history == "Oui":
                risk_factors += 2
            if learning_difficulties == "Oui":
                risk_factors += 1
            if age < 12:
                risk_factors += 1
                
            # Calcul du risque (simulation)
            risk_probability = min(risk_factors / 8.0, 0.95)
            
            # Affichage des résultats
            st.markdown("---")
            st.subheader("📊 Résultats de l'analyse")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Score Inattention", f"{inattention_score}/15")
            with col2:
                st.metric("Score Hyperactivité", f"{hyperactivite_score}/15")
            with col3:
                st.metric("Score Total", f"{total_score}/30")
            
            # Évaluation du risque
            st.subheader("🎯 Évaluation du risque")
            
            if risk_probability > 0.7:
                st.error(f"⚠️ **Risque élevé de TDAH** ({risk_probability:.1%})")
                st.markdown("""
                <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 4px solid #f44336;">
                    <h4 style="color: #c62828; margin-top: 0;">Recommandations :</h4>
                    <ul style="color: #d32f2f;">
                        <li>Consultez rapidement un professionnel de santé spécialisé</li>
                        <li>Documentez les symptômes observés</li>
                        <li>Considérez une évaluation neuropsychologique</li>
                        <li>Informez l'école/employeur si approprié</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            elif risk_probability > 0.4:
                st.warning(f"⚠️ **Risque modéré de TDAH** ({risk_probability:.1%})")
                st.markdown("""
                <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; border-left: 4px solid #ff9800;">
                    <h4 style="color: #ef6c00; margin-top: 0;">Recommandations :</h4>
                    <ul style="color: #f57c00;">
                        <li>Surveillez l'évolution des symptômes</li>
                        <li>Consultez votre médecin traitant</li>
                        <li>Mettez en place des stratégies d'organisation</li>
                        <li>Réévaluez dans quelques semaines</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.success(f"✅ **Risque faible de TDAH** ({risk_probability:.1%})")
                st.markdown("""
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 4px solid #4caf50;">
                    <h4 style="color: #2e7d32; margin-top: 0;">Recommandations :</h4>
                    <ul style="color: #388e3c;">
                        <li>Continuez à surveiller si des préoccupations persistent</li>
                        <li>Maintenez de bonnes habitudes d'organisation</li>
                        <li>N'hésitez pas à refaire le test si les symptômes évoluent</li>
                        <li>Consultez si d'autres difficultés apparaissent</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Graphique des scores
            st.subheader("📈 Visualisation des scores")
            
            scores_data = pd.DataFrame({
                'Dimension': ['Inattention', 'Hyperactivité/Impulsivité'],
                'Score': [inattention_score, hyperactivite_score],
                'Score Max': [15, 15]
            })
            
            fig_scores = go.Figure()
            
            fig_scores.add_trace(go.Bar(
                name='Score obtenu',
                x=scores_data['Dimension'],
                y=scores_data['Score'],
                marker_color='#ff5722'
            ))
            
            fig_scores.add_trace(go.Bar(
                name='Score maximum',
                x=scores_data['Dimension'],
                y=scores_data['Score Max'],
                marker_color='#ffcdd2',
                opacity=0.6
            ))
            
            fig_scores.update_layout(
                title='Répartition des scores par dimension',
                yaxis_title='Score',
                barmode='overlay'
            )
            
            st.plotly_chart(fig_scores, use_container_width=True)
            
            # Avertissement
            st.markdown("""
            <div style="margin: 30px 0; padding: 20px; border-radius: 12px;
                       border-left: 4px solid #f44336; background: linear-gradient(135deg, #ffebee, #ffcdd2);
                       box-shadow: 0 4px 12px rgba(244, 67, 54, 0.1);">
                <p style="font-size: 1rem; color: #c62828; text-align: center; margin: 0; line-height: 1.6;">
                    <strong style="color: #f44336;">⚠️ Important :</strong>
                    Cette analyse est un outil d'aide au dépistage uniquement. 
                    Seul un professionnel de santé qualifié peut poser un diagnostic de TDAH.
                </p>
            </div>
            """, unsafe_allow_html=True)

def show_documentation():
    """Page de documentation pour le TDAH"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            📚 Documentation TDAH
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Guide complet sur le Trouble Déficitaire de l'Attention avec Hyperactivité
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Onglets de documentation
    doc_tabs = st.tabs([
        "📖 Bases du TDAH",
        "🔬 Critères diagnostiques",
        "💊 Traitements",
        "🏫 Accompagnement",
        "📚 Ressources"
    ])

    with doc_tabs[0]:
        st.subheader("📖 Comprendre le TDAH")
        
        st.markdown("""
        <div class="info-card-modern">
            <h3 style="color: #ff5722;">Définition</h3>
            <p>Le TDAH est un trouble neurodéveloppemental caractérisé par un pattern persistant d'inattention 
            et/ou d'hyperactivité-impulsivité qui interfère avec le fonctionnement ou le développement.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🧠 Bases neurobiologiques :**
            - Différences dans le développement du cortex préfrontal
            - Dysfonctionnement des neurotransmetteurs (dopamine, noradrénaline)
            - Composante génétique forte (héritabilité 70-80%)
            - Facteurs environnementaux (prématurité, exposition toxique)
            """)
            
        with col2:
            st.markdown("""
            **📊 Prévalence :**
            - 5-7% des enfants d'âge scolaire
            - 2.5% des adultes
            - Plus fréquent chez les garçons (ratio 3:1)
            - Sous-diagnostiqué chez les filles
            """)

    with doc_tabs[1]:
        st.subheader("🔬 Critères diagnostiques DSM-5")
        
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #ef6c00;">Critères généraux</h4>
            <ul>
                <li>Symptômes présents avant 12 ans</li>
                <li>Présents dans au moins 2 environnements</li>
                <li>Interférence significative avec le fonctionnement</li>
                <li>Non expliqués par un autre trouble</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Symptômes d'inattention** (6+ symptômes pendant 6+ mois) :
            1. Difficulté à maintenir l'attention
            2. Ne semble pas écouter
            3. N'arrive pas à terminer les tâches
            4. Difficulté à organiser
            5. Évite les tâches nécessitant un effort mental
            6. Perd souvent des objets
            7. Facilement distrait
            8. Oublis dans les activités quotidiennes
            9. Néglige les détails, fait des erreurs
            """)
            
        with col2:
            st.markdown("""
            **⚡ Symptômes d'hyperactivité-impulsivité** (6+ symptômes pendant 6+ mois) :
            
            *Hyperactivité :*
            1. Remue mains/pieds, se tortille
            2. Se lève quand devrait rester assis
            3. Court/grimpe de façon inappropriée
            4. Difficulté avec les loisirs calmes
            5. "Toujours en mouvement"
            6. Parle excessivement
            
            *Impulsivité :*
            7. Répond avant la fin des questions
            8. Difficulté à attendre son tour
            9. Interrompt ou impose sa présence
            """)

    with doc_tabs[2]:
        st.subheader("💊 Options de traitement")
        
        treatment_tabs = st.tabs(["Médicaments", "Thérapies", "Interventions"])
        
        with treatment_tabs[0]:
            st.markdown("""
            **Médicaments stimulants :**
            - Méthylphénidate (Ritaline, Concerta)
            - Amphétamines (Adderall, Vyvanse)
            - Efficacité 70-80%
            - Amélioration rapide des symptômes
            
            **Médicaments non-stimulants :**
            - Atomoxétine (Strattera)
            - Guanfacine (Intuniv)
            - Pour patients ne tolérant pas les stimulants
            """)
            
        with treatment_tabs[1]:
            st.markdown("""
            **Thérapie comportementale :**
            - Modification du comportement
            - Techniques de gestion du temps
            - Stratégies d'organisation
            
            **Thérapie cognitive :**
            - Restructuration cognitive
            - Gestion de l'attention
            - Résolution de problèmes
            
            **Thérapie familiale :**
            - Éducation des parents
            - Stratégies de communication
            - Gestion des comportements difficiles
            """)
            
        with treatment_tabs[2]:
            st.markdown("""
            **Adaptations scolaires :**
            - Plan d'accompagnement personnalisé (PAP)
            - Aménagements d'examens
            - Soutien pédagogique spécialisé
            
            **Interventions psychoéducatives :**
            - Groupes de compétences sociales
            - Entraînement aux fonctions exécutives
            - Programmes de pleine conscience
            
            **Modifications environnementales :**
            - Réduction des distracteurs
            - Structure et routine
            - Feedback immédiat
            """)

    with doc_tabs[3]:
        st.subheader("🏫 Accompagnement au quotidien")
        
        accomp_tabs = st.tabs(["À l'école", "En famille", "Au travail"])
        
        with accomp_tabs[0]:
            st.markdown("""
            **Stratégies pédagogiques :**
            - Instructions courtes et claires
            - Pause-mouvement régulières
            - Support visuel
            - Renforcement positif
            
            **Aménagements :**
            - Temps supplémentaire
            - Lieu calme pour les examens
            - Utilisation d'ordinateur
            - Pause durant les évaluations
            """)
            
        with accomp_tabs[1]:
            st.markdown("""
            **Gestion familiale :**
            - Routines structurées
            - Règles claires et cohérentes
            - Système de récompenses
            - Communication positive
            
            **Organisation quotidienne :**
            - Planners visuels
            - Listes de tâches
            - Zones dédiées (devoirs, jeux)
            - Horaires réguliers
            """)
            
        with accomp_tabs[2]:
            st.markdown("""
            **Adaptations professionnelles :**
            - Bureau calme
            - Pauses fréquentes
            - Tâches variées
            - Deadlines flexibles
            
            **Outils d'aide :**
            - Applications de gestion du temps
            - Rappels automatiques
            - Techniques Pomodoro
            - Mind mapping
            """)

    with doc_tabs[4]:
        st.subheader("📚 Ressources utiles")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🏥 Organisations professionnelles :**
            - Association française pour les enfants précoces (AFEP)
            - TDAH France
            - Société française de psychiatrie de l'enfant
            - Centre national de référence des troubles d'apprentissage
            
            **📱 Applications utiles :**
            - Forest (concentration)
            - Todoist (organisation)
            - Brain Focus (Pomodoro)
            - MindMeister (mind mapping)
            """)
            
        with col2:
            st.markdown("""
            **📖 Lectures recommandées :**
            - "TDAH, la boîte à outils" - A. Gremion
            - "Mon cerveau a besoin de lunettes" - A. Houde
            - "L'enfant inattentif et hyperactif" - S. Laporte
            - "TDAH chez l'adulte" - M. Bouvard
            
            **🌐 Sites web :**
            - [TDAH-France.fr](https://www.tdah-france.fr)
            - [HAS - TDAH](https://www.has-sante.fr)
            - [INSERM - TDAH](https://www.inserm.fr)
            """)

def show_about():
    """Page À propos adaptée pour le TDAH"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff5722, #ff9800);
                padding: 40px 25px; border-radius: 20px; margin-bottom: 35px; text-align: center;">
        <h1 style="color: white; font-size: 2.8rem; margin-bottom: 15px;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3); font-weight: 600;">
            ℹ️ À propos de cette plateforme
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 1.3rem;
                  max-width: 800px; margin: 0 auto; line-height: 1.6;">
            Information sur le projet et l'équipe
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card-modern">
        <h2 style="color: #ff5722; text-align: center;">🎯 Mission</h2>
        <p style="font-size: 1.1rem; line-height: 1.8; text-align: center;">
            Améliorer le dépistage précoce du TDAH grâce à l'intelligence artificielle
            et fournir des outils d'aide à la décision pour les professionnels de santé.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card-modern">
            <h3 style="color: #ff5722;">🔬 Méthodologie</h3>
            <ul>
                <li>Analyse de données cliniques</li>
                <li>Modèles de machine learning</li>
                <li>Validation croisée</li>
                <li>Approche evidence-based</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card-modern">
            <h3 style="color: #ff9800;">⚠️ Limitations</h3>
            <ul>
                <li>Outil d'aide uniquement</li>
                <li>Ne remplace pas le diagnostic médical</li>
                <li>Données d'entraînement limitées</li>
                <li>Validation continue nécessaire</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card-modern">
        <h3 style="color: #ff5722; text-align: center;">👥 Équipe</h3>
        <p style="text-align: center; font-size: 1.1rem;">
            Ce projet a été développé par une équipe multidisciplinaire combinant expertise clinique,
            data science et développement logiciel pour créer un outil d'aide au dépistage du TDAH.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Contact et informations
    st.markdown("""
    <div style="margin: 40px 0 30px 0; padding: 20px; border-radius: 12px;
               border-left: 4px solid #ff5722; background: linear-gradient(135deg, #fff3e0, #ffcc02);
               box-shadow: 0 4px 12px rgba(255, 87, 34, 0.1);">
        <p style="font-size: 1rem; color: #ef6c00; text-align: center; margin: 0; line-height: 1.6;">
            <strong>📧 Contact :</strong> Pour toute question ou collaboration, contactez l'équipe de développement.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Application principale
def main():
    set_custom_theme()
    initialize_session_state()
    
    # Sidebar avec navigation
    with st.sidebar:
        selected_tool = show_navigation_menu()

    # Contenu principal basé sur la sélection
    if selected_tool == "🏠 Accueil":
        show_home_page()
    elif selected_tool == "🔍 Exploration":
        show_data_exploration()
    elif selected_tool == "🧠 Analyse ML":
        show_ml_analysis()
    elif selected_tool == "🤖 Prédiction par IA":
        show_ai_prediction()
    elif selected_tool == "📚 Documentation":
        show_documentation()
    elif selected_tool == "ℹ️ À propos":
        show_about()

if __name__ == "__main__":
    main()


