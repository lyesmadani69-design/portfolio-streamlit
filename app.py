# app.py
import base64
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import streamlit as st

# ===================== CONFIG APP =====================
st.set_page_config(page_title="Portfolio Data Analyst", page_icon="📊", layout="wide")

# statsmodels (optionnel)
try:
    from statsmodels.tsa.holtwinters import Holt
except Exception:
    Holt = None  # évite un crash si non installé

# Dossiers ancrés sur le script
BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"
# st.sidebar.write("📂 Contenu du dossier assets :")
# st.sidebar.write([p.name for p in ASSETS.glob("*")])
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"

for d in (ASSETS, DATA_DIR, UPLOADS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# petit état utile pour invalider du cache d'images si besoin
if "assets_version" not in st.session_state:
    st.session_state["assets_version"] = 0


# ===================== HELPERS =====================
def resolve_asset(name: str) -> Path | None:
    """
    Résout un nom/chemin de fichier vers le dossier assets/.
    Accepte:
      - "pareto.png"
      - "assets/pareto.png"
      - chemin absolu
    Corrige aussi l'erreur fréquente "assets-xxx.png" -> "xxx.png".
    """
    if not name:
        return None
    s = str(name).strip()

    # Auto-fix erreurs fréquentes
    if s.startswith("assets-"):
        s = s.replace("assets-", "", 1)

    p = Path(s)

    # Chemin absolu
    if p.is_absolute():
        return p if p.exists() else None

    # Si "assets/xxx", garde juste le nom
    parts = p.parts
    if len(parts) >= 2 and parts[0].lower() == "assets":
        p = Path(parts[-1])

    cand = ASSETS / p.name
    return cand if cand.exists() else None


def show_image_safe(img: str) -> None:
    """Affiche une image depuis URL ou fichier local (sécurisé)."""
    if not img:
        return
    s = str(img)
    if s.startswith(("http://", "https://")):
        st.image(s, use_container_width=True)
        return
    p = resolve_asset(s) or (BASE_DIR / s if (BASE_DIR / s).exists() else None)
    if p and p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning(f"Image introuvable : {img} (cherché dans {ASSETS})")


def pdf_download_button(label: str, report: str, key: str | None = None) -> None:
    """Bouton de téléchargement pour un PDF local (ou lien si URL)."""
    if not report:
        return
    s = str(report)
    if s.startswith(("http://", "https://")):
        st.link_button(label, s, use_container_width=True)
        return
    p = resolve_asset(s) or (BASE_DIR / s if (BASE_DIR / s).exists() else None)
    if p and p.exists():
        st.download_button(
            label,
            data=p.read_bytes(),
            file_name=p.name,
            mime="application/pdf",
            use_container_width=True,
            key=key,
        )
    else:
        st.caption(f"PDF introuvable : {report}")


def save_uploaded_file(dirpath: Path, uploaded_file) -> Path:
    """Sauvegarde un fichier uploadé sans écraser (suffixe _1, _2, ...)."""
    safe_name = Path(uploaded_file.name).name
    dest = dirpath / safe_name
    i = 1
    while dest.exists():
        dest = dirpath / f"{dest.stem}_{i}{dest.suffix}"
        i += 1
    dest.write_bytes(uploaded_file.getbuffer())
    return dest


# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("## À propos")
    portrait = ASSETS / "dash.png"  # remplace par ton fichier si dispo
    if portrait.exists():
        st.image(str(portrait), caption="Lyes", use_container_width=True)
    else:
        st.info("Place une image '' dans assets/ pour l'afficher ici.")

    st.write(
        "Je suis Data Analyst spécialisé en data cleaning, data viz et time series."
    )
    st.write("Basé à Lyon — Disponible en freelance.")

    st.link_button("GitHub", "https://github.com/TON_COMPTE", use_container_width=True)
    st.link_button(
        "LinkedIn", "https://www.linkedin.com/in/TON_PROFIL", use_container_width=True
    )

    cv_path = ASSETS / "CV.pdf"
    if cv_path.exists():
        with open(cv_path, "rb") as f:
            st.download_button(
                "📄 Télécharger mon CV",
                f,
                file_name="CV_TonNom.pdf",
                use_container_width=True,
            )
    else:
        st.caption("Place ton CV dans assets/CV.pdf pour activer le bouton.")
        st.markdown("## 📞 Contact")
        st.write("📧 **Email :** lyesmadani69@gmail.com")
        st.link_button(
            "💼 LinkedIn",
            "https://www.linkedin.com/in/ton-profil",
            use_container_width=True,
        )
        st.link_button(
            "🌐 GitHub",
            "https://github.com/lyesmadani69-design",
            use_container_width=True,
        )

    # Debug chemins (optionnel)
    if st.checkbox("🔧 Debug chemins", value=False):
        st.write("BASE_DIR:", str(BASE_DIR))
        st.write("ASSETS:", str(ASSETS))
        st.write("UPLOADS_DIR:", str(UPLOADS_DIR))
        try:
            st.write("Contenu assets:", [p.name for p in ASSETS.glob("*")])
        except Exception:
            pass


# ===================== HEADER =====================
st.title("Data Analyst Freelance")
st.subheader("J’aide les commerces et petites entreprises à exploiter leurs données")

st.write(
    """
Je transforme des fichiers Excel et CSV bruts en tableaux de bord clairs, indicateurs utiles
et recommandations concrètes pour faciliter la prise de décision.

Mes spécialités :
- nettoyage et structuration de données
- analyse des ventes, stocks et KPI
- dashboards interactifs
- prévisions et analyse des tendances
"""
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Expertise", "Data cleaning")
c2.metric("Spécialités", "Ventes • KPI")
c3.metric("Livrables", "Dashboards")
c4.metric("Statut", "Freelance")

#
#  ===================== TABS =====================clients (RFM) • A/B tests."
# ===================== HOME =====================
tab_home, tab_projects, tab_skills, tab_contact, tab_smooth, tab_gallery, tab_readme = (
    st.tabs(
        [
            "Accueil",
            "Projets",
            "Compétences",
            "Contact",
            "Prévision",
            "Galerie",
            "Présentation",
        ]
    )
)


with tab_home:
    st.subheader("Bienvenue")

    st.write(
        """
Je suis Data Analyst freelance basé à Lyon.

J’aide les commerces, indépendants et petites entreprises à transformer leurs fichiers bruts
en tableaux de bord lisibles, indicateurs utiles et analyses exploitables.
"""
    )

    st.markdown("### Ce que je peux vous apporter")
    st.markdown(
        """
- nettoyer et fiabiliser vos données
- analyser vos ventes, stocks ou performances
- créer des dashboards simples à utiliser
- repérer les anomalies, tendances et produits clés
- fournir un reporting clair pour la prise de décision
"""
    )

    st.markdown("### Outils")
    st.write("Python • Excel • SQL • Power BI • Streamlit")

    st.markdown("### Cas d’usage")
    st.write(
        """
Exports caisse, fichiers de ventes, suivi de stock, prestations, reporting d’activité,
analyse temporelle et prévisions.
"""
    )


# ===================== PROJECTS =====================
PROJECTS = [
    {
        "title": "Analyse des ventes d’un commerce",
        "summary": "Nettoyage d’exports caisse, calcul des KPI clés, analyse Pareto et suivi des ventes dans le temps pour identifier les produits les plus rentables.",
        "skills": ["Python", "Pandas", "Matplotlib", "Streamlit"],
        "image": "kpi-four.png",
        "report": "pareto.pdf",
        "extras": ["assets-pareto.png"],
        "repo": "https://github.com/lyesmadani69-design/caisse-dashboard",
        "demo": "",
    },
    {
        "title": "Analyse métier d’un salon / prestations",
        "summary": "Contrôle des données, vérification des prix, structuration des prestations et visualisation d’indicateurs utiles à l’activité.",
        "skills": ["Python", "Pandas", "Data Cleaning"],
        "image": "dash.png",
        "report": "ventes.mensuel.pdf",
        "extras": [],
        "repo": "https://github.com/lyesmadani69-design/seyanna-dashboard",
        "demo": "",
    },
]


# ===================== SKILLS (placeholder simple) =====================
with tab_skills:
    st.subheader("🛠️ Compétences")

    st.write(
        """
    Voici une vue d'ensemble de mes compétences en Data :
    - **Python** : pandas, numpy, statsmodels
    - **SQL** : requêtes analytiques
    - **Data-viz** : Matplotlib, Plotly, BI (Power BI)
    - **Time series** : Holt, Holt-Winters, optimisation des coefficients
    - **KPI & métriques** : MAE, RMSE, MAPE
    - **Machine Learning** : RandomForest, classification, régression
    - **Reporting automatisé** : Markdown + PDF
    """
    )

    # 🔗 Schéma pipeline
    st.image(
        "assets/pipeline.png",
        caption="Pipeline d'analyse & imputation",
        use_container_width=True,
    )

    # 📸 Aperçu du rapport (capture PNG)
    st.image(
        "assets/rapport_2025.png",
        caption="Aperçu du rapport 2025",
        use_container_width=True,
    )

    # 📥 Bouton pour télécharger le rapport complet en PDF
    with open("assets/rapport_2025.pdf", "rb") as pdf_file:
        st.download_button(
            label="📥 Télécharger le rapport complet (PDF)",
            data=pdf_file,
            file_name="rapport_2025.pdf",
            mime="application/pdf",
        )


# ===================== CONTACT (placeholder) =====================
with tab_contact:
    st.subheader("📮 Contact")
    st.write("Envoyez-moi un message sur LinkedIn ou GitHub (liens dans la sidebar).")
    st.write("Possibilité d'intervenir en mission freelance, sur devis.")


# ===================== TAB SMOOTH (Holt) =====================
with tab_smooth:
    st.subheader("📈 Lissage exponentiel double (méthode de Holt)")
    st.caption(f"Dossier des données persistantes : {UPLOADS_DIR.resolve()}")

    # Upload
    up = st.file_uploader(
        "Charger un CSV ou Excel",
        type=["csv", "xlsx"],
        key="smooth_up",
        help="Charge un fichier .csv ou .xlsx ; il sera copié dans le dossier de persistance.",
    )
    load_path = None
    if up is not None:
        dest = save_uploaded_file(UPLOADS_DIR, up)
        st.success(f"Fichier enregistré : {dest.name}")
        st.session_state["last_data_file"] = str(dest)

    # Fichiers existants
    saved_files = sorted(
        list(UPLOADS_DIR.glob("*.csv")) + list(UPLOADS_DIR.glob("*.xlsx")),
        key=lambda p: p.name.lower(),
    )
    saved_names = [p.name for p in saved_files]
    default_idx = 0
    if "last_data_file" in st.session_state:
        last = Path(st.session_state["last_data_file"]).name
        if last in saved_names:
            default_idx = saved_names.index(last)

    if saved_files:
        selected_name = st.selectbox(
            "Ou choisir un fichier enregistré",
            saved_names,
            index=default_idx,
            key="smooth_pick_saved",
        )
        load_path = UPLOADS_DIR / selected_name
        st.caption(f"✅ Fichier sélectionné : {load_path.name}")
    else:
        st.info(
            "Aucun fichier enregistré pour l’instant. Charge un CSV/Excel ci-dessus ou utilise l’exemple."
        )

    # Exemple
    use_example = st.checkbox(
        "Utiliser un jeu d'exemple",
        value=(load_path is None and up is None),
        key="smooth_use_example",
    )

    # ===== Lecture dataset -> df (2 if séparés, pas d'elif) =====
    df = None

    # 1) Lecture du fichier sélectionné
    if (load_path is not None) and load_path.exists():
        try:
            if load_path.suffix.lower() == ".csv":
                df = pd.read_csv(load_path)
            else:
                df = pd.read_excel(load_path)  # nécessite openpyxl
        except Exception as e:
            st.error(f"Impossible de lire {load_path.name} : {e}")
            df = None

    # 2) Exemple si df encore vide
    if (df is None) and use_example:
        dates = pd.date_range("2022-01-01", periods=36, freq="MS")
        values = (
            200
            + np.arange(36) * 3
            + np.sin(np.arange(36) / 6) * 10
            + np.random.normal(0, 5, 36)
        )
        df = pd.DataFrame({"date": dates, "valeur": values})
        st.caption("📦 Exemple 36 mois. Charge un fichier pour utiliser tes données.")

    # Info si toujours rien
    if df is None and not use_example:
        st.info("Charge un fichier ou coche 'Utiliser un jeu d'exemple'.")

    # ===== Garde =====
    if df is None:
        pass
    else:
        # Sélection colonnes
        cols = list(df.columns)
        default_date_col = "date" if "date" in cols else cols[0]
        numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        default_val_col = (
            "valeur"
            if "valeur" in cols
            else (numeric_cols[0] if numeric_cols else cols[-1])
        )

        st.markdown("### ⚙️ Paramètres & colonnes")
        c1, c2 = st.columns(2)
        with c1:
            col_date = st.selectbox(
                "Colonne date / temps", cols, index=cols.index(default_date_col)
            )
            parse_date = st.checkbox("Convertir en datetime (to_datetime)", value=True)
        with c2:
            col_val = st.selectbox(
                "Colonne valeur", cols, index=cols.index(default_val_col)
            )

        # Préparation série
        s_df = df[[col_date, col_val]].copy()
        if parse_date:
            s_df[col_date] = pd.to_datetime(s_df[col_date], errors="coerce")
        s_df = (
            s_df.dropna(subset=[col_date, col_val])
            .sort_values(col_date)
            .reset_index(drop=True)
        )

        # Fréquence (pour horizon futur)
        try:
            inferred = pd.infer_freq(s_df[col_date])
        except Exception:
            inferred = None
        freq_choices = ["D", "W", "MS", "M", "Q", "Y"]
        default_freq_idx = freq_choices.index("MS")
        st.caption(
            f"Fréquence inférée : **{inferred}**"
            if inferred
            else "Fréquence non inférée."
        )
        freq = st.selectbox(
            "Fréquence pour la prévision future",
            freq_choices,
            index=(
                freq_choices.index(inferred)
                if inferred in freq_choices
                else default_freq_idx
            ),
            help="Utilisée pour générer les dates futures (prévisions).",
        )

        st.markdown("### 🔧 Holt (double lissage)")
        c3, c4, c5 = st.columns(3)
        with c3:
            optimized = st.toggle(
                "Optimiser automatiquement",
                value=True,
                help="Si activé, ignore alpha/beta.",
            )
        with c4:
            alpha = st.slider("alpha (niveau)", 0.01, 0.99, 0.50, 0.01)
        with c5:
            beta = st.slider("beta (tendance)", 0.01, 0.99, 0.10, 0.01)

        c6, c7 = st.columns(2)
        with c6:
            damped = st.checkbox("Tendance amortie (damped_trend)", value=False)
        with c7:
            horizon = st.number_input(
                "Horizon de prévision (pas de temps)",
                min_value=1,
                max_value=120,
                value=12,
                step=1,
            )

        st.markdown("### 👀 Aperçu des données")
        st.dataframe(s_df.head(10))

        if Holt is None:
            st.warning(
                "Le module Holt (statsmodels) n'est pas disponible. Installe-le : `pip install statsmodels`"
            )
        else:
            if st.button("🚀 Appliquer Holt et tracer"):
                try:
                    y = pd.Series(
                        s_df[col_val].astype(float).values,
                        index=pd.Index(s_df[col_date].values, name=col_date),
                    )

                    model = Holt(y, exponential=False, damped_trend=damped)
                    if optimized:
                        fit = model.fit(optimized=True)
                    else:
                        fit = model.fit(
                            smoothing_level=float(alpha),
                            smoothing_slope=float(beta),
                            optimized=False,
                        )

                    # Prévisions futures
                    last_dt = s_df[col_date].iloc[-1]
                    future_index = pd.date_range(
                        start=last_dt, periods=horizon + 1, freq=freq
                    )[1:]
                    fcst = fit.forecast(horizon)
                    try:
                        fcst.index = future_index
                    except Exception:
                        fcst = pd.Series(
                            fcst.values, index=future_index, name="forecast"
                        )

                    observed = y.rename("observé")
                    fitted = fit.fittedvalues.rename("lissé")
                    forecast = pd.Series(
                        fcst.values, index=fcst.index, name="prévision"
                    )

                    df_plot = pd.concat([observed, fitted], axis=1)
                    df_plot = pd.concat([df_plot, forecast], axis=1)

                    st.markdown("### 📊 Série, lissé et prévisions")
                    st.line_chart(df_plot)

                    # Métriques
                    sse = getattr(fit, "sse", np.nan)
                    aic = getattr(fit, "aic", np.nan)
                    bic = getattr(fit, "bic", np.nan)
                    llf = getattr(fit, "llf", np.nan)

                    c8, c9, c10, c11 = st.columns(4)
                    c8.metric("SSE", f"{sse:,.2f}")
                    c9.metric("AIC", f"{aic:,.2f}" if pd.notna(aic) else "n/a")
                    c10.metric("BIC", f"{bic:,.2f}" if pd.notna(bic) else "n/a")
                    c11.metric(
                        "Log-Likelihood", f"{llf:,.2f}" if pd.notna(llf) else "n/a"
                    )

                    # Export CSV
                    exp = pd.DataFrame(
                        {
                            col_date: list(observed.index) + list(forecast.index),
                            "observé": list(observed.values) + [np.nan] * len(forecast),
                            "lissé": list(fitted.reindex(observed.index).values)
                            + [np.nan] * len(forecast),
                            "prévision": [np.nan] * len(observed)
                            + list(forecast.values),
                        }
                    )
                    st.download_button(
                        "💾 Télécharger (observé/lissé/prévision .csv)",
                        exp.to_csv(index=False).encode("utf-8"),
                        file_name="holt_resultats.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Erreur pendant l'entraînement Holt ou le tracé : {e}")

    # --- fin de l'onglet Lissage exp. ---

    st.subheader("📸 Schéma du double lissage")
    img_path = ASSETS / "doubleliss.png"
    if img_path.exists():
        st.image(
            str(img_path), caption="Méthode du double lissage", use_container_width=True
        )
    else:
        st.warning("Image 'doubleliss.png' manquante dans assets/")


# ===================== GALLERY =====================
with tab_gallery:
    st.subheader("🖼️ Galerie")

    # Upload d'images
    img_up = st.file_uploader(
        "Ajouter une image (png/jpg/jpeg/webp/gif)",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        key="img_gallery",
    )
    if img_up is not None:
        dest = save_uploaded_file(ASSETS, img_up)
        st.success(f"Ajouté : {dest.name}")
        st.image(str(dest), use_container_width=True)

    # Grille d'images
    exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    images = sorted([p for p in ASSETS.glob("*") if p.suffix.lower() in exts])
    if not images:
        st.info(
            "Aucune image trouvée. Place des fichiers dans assets/ ou utilise l’upload ci-dessus."
        )
    else:
        cols = st.columns(3)
        for i, p in enumerate(images):
            with cols[i % 3]:
                st.image(str(p), caption=p.name, use_container_width=True)

    st.write("---")

    # Image spécifique : grille Holt + interprétation (optionnel)
    st.subheader("📸 Grille de recherche Holt (α–β)")
    grid_path = ASSETS / "opti-coeff.png"  # place ce fichier dans assets/
    if grid_path.exists():
        st.image(
            str(grid_path),
            use_container_width=True,
            caption="Erreur par couple (α, β) — plus bas = mieux",
        )
        st.markdown(
            r"""
**Interprétation (opti par RMSE).**
Évaluation d'une grille de couples \((\alpha,\beta)\) avec calcul de la **RMSE** pour chacun.
La **RMSE la plus faible** est obtenue pour un couple \(\alpha\) élevé et \(\beta\) faible : niveau réactif, tendance lissée.
*Valider sur un jeu de test pour confirmer la performance hors-échantillon.*
"""
        )
    else:
        st.info(f"Place l'image 'opti-coeff.png' dans {ASSETS} pour l'afficher ici.")

    st.write("---")

    # PDF (upload + téléchargement + aperçu)
    # --- PDF (upload + téléchargement + aperçu robuste) ---

st.subheader("📄 Rapports (PDF)")
pdf_up = st.file_uploader("Ajouter un PDF", type=["pdf"], key="pdf_uploader")
if pdf_up is not None:
    dest = ASSETS / pdf_up.name
    i = 1
    while dest.exists():
        dest = ASSETS / f"{Path(pdf_up.name).stem}_{i}.pdf"
        i += 1
    dest.write_bytes(pdf_up.getbuffer())
    st.success(f"Ajouté : {dest.name}")

pdfs = sorted(ASSETS.glob("*.pdf"), key=lambda p: p.name.lower())
if not pdfs:
    st.info("Aucun PDF trouvé. Dépose des fichiers ici ou place-les dans assets/.")
else:
    for p in pdfs:
        with st.container(border=True):
            st.write(f"**{p.name}**")

            # Bouton télécharger (100% fiable)
            st.download_button(
                "💾 Télécharger",
                data=p.read_bytes(),
                file_name=p.name,
                mime="application/pdf",
                key=f"dl_{p.name}",
                use_container_width=True,
            )

            # Aperçu image (1ʳᵉ page) pour contourner les blocages iframe
            show_preview = st.toggle("🔍 Aperçu", key=f"prev_{p.name}")
            if show_preview:
                try:
                    import fitz  # PyMuPDF

                    doc = fitz.open(p)  # peut ouvrir via Path
                    page = doc.load_page(0)  # première page
                    pix = page.get_pixmap(dpi=144)  # résolution correcte
                    img_bytes = pix.tobytes("png")
                    st.image(
                        img_bytes,
                        use_container_width=True,
                        caption=f"Prévisualisation — {p.name}",
                    )
                    doc.close()
                except Exception:
                    # Fallback: tenter l'iframe base64 (peut être bloqué par le navigateur)
                    st.info(
                        "Prévisualisation image indisponible, tentative en iframe (peut être bloquée par votre navigateur)."
                    )
                    import base64

                    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>',
                        unsafe_allow_html=True,
                    )

# ------------------------------------------------------------
# Onglet Présentation (affiche ton README.md)
# ------------------------------------------------------------
with tab_readme:
    st.subheader("📖 Présentation du Portfolio")

    readme_path = BASE_DIR / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
        st.markdown(readme_content, unsafe_allow_html=True)
    else:
        st.warning("Le fichier README.md est introuvable dans le projet.")
