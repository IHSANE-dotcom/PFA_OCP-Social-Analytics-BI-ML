"""
Segmentation Comportementale des Agents & Affectation au Segment
Programme d'Estivage OCP - Site de Khouribga - Campagne 2026

Application Streamlit dédiée à la prédiction des segments comportementaux.
Lancer avec : streamlit run app.py

Fichiers requis dans le meme dossier :
  - agents_segmentes22.csv
  - metrics.json
  - form_options.json
  - model_pipeline.joblib
  - OIp.png (logo OCP)
"""
import json
import joblib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import chi2_contingency, kruskal
import base64
from pathlib import Path

# =============================================================================
# CONFIGURATION GENERALE
# =============================================================================

# Chargement du logo pour la page
def get_logo_base64():
    logo_path = Path("OIp.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_BASE64 = get_logo_base64()

# Configuration de la page avec le logo
page_icon = "◆"
if LOGO_BASE64:
    page_icon = f"data:image/png;base64,{LOGO_BASE64}"

st.set_page_config(
    page_title="OCP Estivage — Prédiction des Segments",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# PALETTE DE COULEURS MODERNISEE
# =============================================================================
INK = "#1A1A2E"
INK_SOFT = "#4A4A6A"
BG = "#F0F2F5"
CARD = "#FFFFFF"
BORDER = "#E8ECF1"
PRIMARY = "#1B4D3E"
PRIMARY_LIGHT = "#2A7A5C"
PRIMARY_GRADIENT = "linear-gradient(135deg, #1B4D3E 0%, #2A7A5C 100%)"
PRIMARY_SOFT = "#E8F3EE"
ACCENT = "#C49B3F"
ACCENT_LIGHT = "#F5E6C8"
BLUE = "#3A7CA5"
BLUE_SOFT = "#E3EEF5"
RED_SOFT = "#C44536"
GREEN = "#27AE60"
GREEN_SOFT = "#E8F8EE"

SEGMENT_ORDER = [
    "Sejours Longs et Budget Premium",
    "Veterans a Faible Frequence",
    "Utilisateurs Frequents et Economes",
]

PERSONA_COLORS = {
    "Sejours Longs et Budget Premium": PRIMARY_LIGHT,
    "Veterans a Faible Frequence": ACCENT,
    "Utilisateurs Frequents et Economes": BLUE,
}

PERSONA_GRADIENTS = {
    "Sejours Longs et Budget Premium": "linear-gradient(135deg, #1B4D3E, #2A7A5C)",
    "Veterans a Faible Frequence": "linear-gradient(135deg, #C49B3F, #D4A843)",
    "Utilisateurs Frequents et Economes": "linear-gradient(135deg, #3A7CA5, #5B9BC7)",
}

PERSONA_SHORT = {
    "Sejours Longs et Budget Premium": "Séjours longs & budget premium",
    "Veterans a Faible Frequence": "Vétérans à faible fréquence",
    "Utilisateurs Frequents et Economes": "Utilisateurs fréquents & économes",
}

PERSONA_TAG = {
    "Sejours Longs et Budget Premium": "Segment Premium",
    "Veterans a Faible Frequence": "Segment Vétéran",
    "Utilisateurs Frequents et Economes": "Segment Économe",
}

PERSONA_DESCRIPTIONS = {
    "Sejours Longs et Budget Premium": (
        "Séjours les plus longs (9,3 nuits en moyenne) et coût par personne le plus élevé. "
        "Taux d'acceptation intermédiaire."
    ),
    "Veterans a Faible Frequence": (
        "Ancienneté et points cumulés les plus élevés ; dernier séjour le plus ancien en moyenne. "
        "Quasi certains d'être acceptés."
    ),
    "Utilisateurs Frequents et Economes": (
        "Ancienneté et points les plus faibles, séjour le plus récent, budget le plus économe. "
        "Taux d'acceptation le plus bas des trois segments."
    ),
}

TAILLE_FOYER_MAP = {"Individuel": 1, "Couple": 2, "Petite famille": 3.5, "Grande famille": 5.5}

# =============================================================================
# STYLE MODERNISE
# =============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    html, body, [class*="css"] {{
        color: {INK};
        background: {BG};
    }}
    
    .main {{
        background: {BG};
    }}
    
    /* Sidebar moderne */
    section[data-testid="stSidebar"] {{
        background: {PRIMARY_GRADIENT};
        border-right: none;
        box-shadow: 4px 0 20px rgba(0,0,0,0.15);
    }}
    
    section[data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    
    section[data-testid="stSidebar"] hr {{
        border-top: 1px solid rgba(255,255,255,0.15);
        margin: 1rem 0;
    }}
    
    /* Sidebar logo et en-tête */
    .sidebar-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0 4px 0;
    }}
    
    .sidebar-header img {{
        height: 48px;
        width: auto;
        filter: brightness(0) invert(1);
    }}
    
    .sidebar-header .title {{
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }}
    
    .sidebar-header .subtitle {{
        font-size: 0.7rem;
        opacity: 0.7;
        font-weight: 400;
        letter-spacing: 0.02em;
    }}
    
    /* Header principal avec logo intégré */
    .app-header {{
        background: {CARD};
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 28px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border: 1px solid {BORDER};
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    
    .app-header:hover {{
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }}
    
    .app-header .header-logo {{
        flex-shrink: 0;
        height: 50px;
        width: auto;
        object-fit: contain;
    }}
    
    .app-header .header-content {{
        flex: 1;
    }}
    
    .app-header .eyebrow {{
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.65rem;
        color: {PRIMARY_LIGHT};
        font-weight: 700;
        margin-bottom: 2px;
    }}
    
    .app-header h1 {{
        margin: 0;
        font-size: 1.5rem;
        color: {INK};
        font-weight: 800;
        letter-spacing: -0.02em;
    }}
    
    .app-header p {{
        margin: 4px 0 0 0;
        color: {INK_SOFT};
        font-size: 0.88rem;
        font-weight: 400;
        line-height: 1.5;
    }}
    
    /* Formulaire moderne */
    .form-section {{
        background: {CARD};
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid {BORDER};
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }}
    
    .form-section h3 {{
        font-size: 0.9rem;
        font-weight: 700;
        color: {PRIMARY};
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Result card */
    .result-card {{
        background: {CARD};
        border-radius: 16px;
        padding: 28px 32px;
        border: 1px solid {BORDER};
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        margin-top: 24px;
        transition: all 0.3s ease;
    }}
    
    .result-card:hover {{
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }}
    
    .result-badge {{
        display: inline-block;
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        color: white;
        letter-spacing: 0.03em;
    }}
    
    .result-title {{
        font-size: 1.3rem;
        font-weight: 800;
        color: {INK};
        margin: 8px 0 4px 0;
    }}
    
    .result-desc {{
        color: {INK_SOFT};
        font-size: 0.9rem;
        line-height: 1.6;
    }}
    
    .result-stats {{
        display: flex;
        gap: 24px;
        margin-top: 12px;
        flex-wrap: wrap;
    }}
    
    .result-stat {{
        background: {PRIMARY_SOFT};
        border-radius: 10px;
        padding: 10px 18px;
    }}
    
    .result-stat .label {{
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {PRIMARY_LIGHT};
        font-weight: 600;
    }}
    
    .result-stat .value {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {INK};
    }}
    
    /* Boutons modernisés */
    .stButton button {{
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        background: {PRIMARY_GRADIENT} !important;
        color: white !important;
        border: none !important;
    }}
    
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(27, 77, 62, 0.3) !important;
    }}
    
    /* Métriques modernisées */
    div[data-testid="stMetric"] {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }}
    
    div[data-testid="stMetric"]:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }}
    
    div[data-testid="stMetricLabel"] {{
        color: {INK_SOFT};
        font-weight: 600;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    
    div[data-testid="stMetricValue"] {{
        color: {INK};
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.01em;
    }}
    
    /* Selectbox et inputs */
    .stSelectbox > div, .stTextInput > div, .stNumberInput > div {{
        border-radius: 10px !important;
    }}
    
    .stSelectbox label, .stTextInput label, .stNumberInput label {{
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: {INK_SOFT} !important;
    }}
    
    /* Slider */
    .stSlider label {{
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: {INK_SOFT} !important;
    }}
    
    /* Hide default elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {BG};
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {PRIMARY_LIGHT};
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {PRIMARY};
    }}
</style>
""", unsafe_allow_html=True)


def style_fig(fig, height=320):
    fig.update_layout(
        font_family="Inter, sans-serif",
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=-0.15),
        hoverlabel=dict(font_family="Inter, sans-serif"),
    )
    fig.update_xaxes(gridcolor="#EDEFE9", showgrid=True, gridwidth=0.5)
    fig.update_yaxes(gridcolor="#EDEFE9", showgrid=True, gridwidth=0.5)
    return fig


def page_header(eyebrow, title, subtitle):
    logo_html = ""
    if LOGO_BASE64:
        logo_html = f'<img src="data:image/png;base64,{LOGO_BASE64}" class="header-logo" alt="OCP Logo">'
    
    st.markdown(
        f"""<div class="app-header">
            {logo_html}
            <div class="header-content">
                <div class="eyebrow">◆ {eyebrow}</div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def fmt_mad(x):
    return f"{x/1_000_000:.2f} M MAD" if abs(x) >= 1_000_000 else f"{x:,.0f} MAD".replace(",", " ")


# =============================================================================
# CHARGEMENT DES DONNEES ET ARTEFACTS
# =============================================================================
@st.cache_data
def load_data():
    df = pd.read_csv("agents_segmentes22.csv", encoding="utf-8-sig")
    df["persona_short"] = df["persona"].map(PERSONA_SHORT)
    df["taille_foyer_estimee"] = df["categorie_taille_groupe"].map(TAILLE_FOYER_MAP)
    df["montant_estime_total"] = df["cout_par_personne"] * df["taille_foyer_estimee"] * df["nombre_demandes"]
    df["charge_ocp_estimee"] = df["montant_estime_total"] * df["taux_prise_charge_ocp"] / 100
    return df


@st.cache_data
def load_metrics():
    with open("metrics.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_form_options():
    with open("form_options.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def load_model():
    return joblib.load("model_pipeline.joblib")


agent_df = load_data()
metrics = load_metrics()
form_options = load_form_options()
model = load_model()

color_map_short = {PERSONA_SHORT[k]: v for k, v in PERSONA_COLORS.items()}
order_short = [PERSONA_SHORT[p] for p in SEGMENT_ORDER]

low_acc_segment = agent_df.groupby("persona")["taux_acceptation"].mean().idxmin()
low_acc_value = agent_df.groupby("persona")["taux_acceptation"].mean().min() * 100

fin_summary = agent_df.groupby("persona").agg(
    n_agents=("matricule", "count"),
    montant_total=("montant_estime_total", "sum"),
    charge_ocp=("charge_ocp_estimee", "sum"),
    taux_acceptation=("taux_acceptation", "mean"),
).reindex(SEGMENT_ORDER)
fin_summary["pct_montant"] = fin_summary["montant_total"] / fin_summary["montant_total"].sum() * 100
fin_summary["pct_agents"] = fin_summary["n_agents"] / fin_summary["n_agents"].sum() * 100


# =============================================================================
# PAGE PRINCIPALE - PREDICTION
# =============================================================================
page_header(
    "Outil d'affectation comportementale",
    "Prédiction du Segment d'un Agent",
    "Affectez un agent à son segment comportemental en renseignant son profil RH et ses choix de demande.",
)

# Métriques de contexte
c1, c2, c3, c4 = st.columns(4)
c1.metric("🎯 Accuracy du modèle", f"{metrics['classification_report']['accuracy']*100:.1f} %")
c2.metric("📊 Segments disponibles", "3")
c3.metric("👥 Agents segmentés", f"{metrics['n_agents']:,}".replace(",", " "))
c4.metric("💰 Budget total estimé", fmt_mad(fin_summary["montant_total"].sum()))

# =============================================================================
# FORMULAIRE DE PREDICTION
# =============================================================================
with st.form("prediction_form", clear_on_submit=False):
    
    # Section 1 : Profil RH
    st.markdown("""
        <div class="form-section">
            <h3>👤 Profil RH de l'agent</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    genre = col1.selectbox("Genre", form_options["genre"])
    situation_familiale = col2.selectbox("Situation familiale", form_options["situation_familiale"])
    categorie_professionnelle = col3.selectbox("Catégorie professionnelle", form_options["categorie_professionnelle"])
    categorie_anciennete = col4.selectbox("Catégorie d'ancienneté", form_options["categorie_anciennete"])
    
    col5, col6 = st.columns(2)
    nombre_points = col5.number_input(
        "Nombre de points", 
        min_value=0, 
        max_value=500, 
        value=180,
        help="Points de fidélité cumulés par l'agent"
    )
    annees_depuis_dernier_sejour = col6.number_input(
        "Années depuis le dernier séjour", 
        min_value=0.0, 
        max_value=15.0, 
        value=2.5, 
        step=0.5,
        help="Nombre d'années écoulées depuis le dernier séjour"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Section 2 : Choix de la demande
    st.markdown("""
        <div class="form-section">
            <h3>🏨 Choix déclarés dans la demande</h3>
    """, unsafe_allow_html=True)
    
    col7, col8, col9 = st.columns(3)
    type_produit = col7.selectbox("Type de produit", form_options["type_produit"])
    ville = col8.selectbox("Ville", form_options["ville"])
    saison = col9.selectbox("Saison", form_options["saison"])
    
    col10, col11, col12 = st.columns(3)
    formule_restauration = col10.selectbox("Formule de restauration", form_options["formule_restauration"])
    type_vue = col11.selectbox("Type de vue", form_options["type_vue"])
    nombre_nuitees = col12.number_input("Nombre de nuitées", min_value=1, max_value=21, value=7)
    
    anticipation_reservation_jours = st.slider(
        "Anticipation de réservation (jours avant le séjour)", 
        min_value=0, 
        max_value=120, 
        value=40,
        help="Nombre de jours entre la réservation et le début du séjour"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Bouton de soumission
    submitted = st.form_submit_button("🎯 Prédire le segment", type="primary", use_container_width=True)

# =============================================================================
# TRAITEMENT DU RESULTAT
# =============================================================================
if submitted:
    # Création du dataframe pour la prédiction
    nouvel_agent = pd.DataFrame([{
        "genre": genre,
        "situation_familiale": situation_familiale,
        "categorie_professionnelle": categorie_professionnelle,
        "categorie_anciennete": categorie_anciennete,
        "type_produit": type_produit,
        "ville": ville,
        "saison": saison,
        "formule_restauration": formule_restauration,
        "type_vue": type_vue,
        "nombre_points": nombre_points,
        "annees_depuis_dernier_sejour": annees_depuis_dernier_sejour,
        "nombre_nuitees": nombre_nuitees,
        "anticipation_reservation_jours": anticipation_reservation_jours,
    }])
    
    # Prédiction
    segment_pred = int(model.predict(nouvel_agent)[0])
    proba = model.predict_proba(nouvel_agent)[0]
    classes = model.classes_
    persona_pred = metrics["personas"][str(segment_pred)]
    color_pred = PERSONA_COLORS[persona_pred]
    gradient_pred = PERSONA_GRADIENTS[persona_pred]
    
    # Affichage du résultat
    st.markdown("---")
    st.markdown("### 📊 Résultat de la prédiction")
    
    col_result, col_prob = st.columns([3, 2])
    
    with col_result:
        st.markdown(
            f"""<div class="result-card" style="border-left: 6px solid {color_pred};">
                <div class="result-badge" style="background:{gradient_pred};">{PERSONA_TAG[persona_pred]}</div>
                <div class="result-title">{PERSONA_SHORT[persona_pred]}</div>
                <div class="result-desc">{PERSONA_DESCRIPTIONS[persona_pred]}</div>
                <div class="result-stats">
                    <div class="result-stat">
                        <div class="label">Confiance</div>
                        <div class="value">{proba.max()*100:.1f}%</div>
                    </div>
                    <div class="result-stat">
                        <div class="label">Taux d'acceptation moyen</div>
                        <div class="value">{agent_df[agent_df['persona']==persona_pred]['taux_acceptation'].mean()*100:.0f}%</div>
                    </div>
                    <div class="result-stat">
                        <div class="label">Nuitées moyennes</div>
                        <div class="value">{agent_df[agent_df['persona']==persona_pred]['nombre_nuitees'].mean():.1f}</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    
    with col_prob:
        proba_df = pd.DataFrame({
            "Segment": [PERSONA_SHORT[metrics["personas"][c]] for c in classes],
            "Probabilité (%)": proba * 100,
        }).sort_values("Probabilité (%)", ascending=True)
        
        fig = px.bar(
            proba_df,
            x="Probabilité (%)",
            y="Segment",
            orientation="h",
            text_auto=".1f",
            color="Segment",
            color_discrete_map=color_map_short,
            category_orders={"Segment": order_short}
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="Probabilité (%)",
            yaxis_title="",
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        fig.update_xaxes(range=[0, 100], gridcolor="#EDEFE9")
        fig.update_yaxes(gridcolor="#EDEFE9")
        st.plotly_chart(fig, use_container_width=True)
    
    # Informations complémentaires
    with st.expander("📖 En savoir plus sur les segments"):
        col_a, col_b, col_c = st.columns(3)
        for col, persona in zip([col_a, col_b, col_c], SEGMENT_ORDER):
            n = (agent_df["persona"] == persona).sum()
            pct = n / len(agent_df) * 100
            with col:
                st.markdown(
                    f"""<div class="card" style="border-top: 3px solid {PERSONA_COLORS[persona]}; padding: 16px 18px;">
                        <div style="font-weight: 700; font-size: 0.9rem; color: {INK};">{PERSONA_SHORT[persona]}</div>
                        <div style="font-size: 0.75rem; color: {INK_SOFT}; margin: 4px 0;">
                            {n} agents · {pct:.1f}%
                        </div>
                        <div style="font-size: 0.8rem; color: {INK_SOFT}; line-height: 1.5;">
                            {PERSONA_DESCRIPTIONS[persona]}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

# =============================================================================
# FOOTER INFORMATIF
# =============================================================================
st.markdown("---")
st.caption(
    "🔬 Modèle entraîné sur les données de la campagne 2026 · "
    "Accuracy : {:.1f}% · {} segments identifiés".format(
        metrics['classification_report']['accuracy']*100,
        len(SEGMENT_ORDER)
    )
)