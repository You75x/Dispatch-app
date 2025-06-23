
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Dispatching", layout="wide")

st.title("🛻 Application de Dispatching Simplifié")
st.markdown("Ajoute tes adresses de **collecte** et **livraison** avec les horaires, puis visualise la tournée optimisée sur une carte.")

# Initialisation
if "taches" not in st.session_state:
    st.session_state.taches = []

# Ajout d'une tâche
with st.form("ajouter_tache"):
    col1, col2 = st.columns(2)
    with col1:
        type_tache = st.selectbox("Type", ["Collecte", "Livraison"])
        heure = st.time_input("Heure prévue")
        priorite = st.selectbox("Priorité", [1, 2, 3])
    with col2:
        adresse = st.text_input("Adresse complète")
        commentaire = st.text_input("Commentaire (optionnel)")

    submitted = st.form_submit_button("➕ Ajouter")
    if submitted and adresse:
        st.session_state.taches.append({
            "Type": type_tache,
            "Adresse": adresse,
            "Heure": heure.strftime("%H:%M"),
            "Priorité": priorite,
            "Commentaire": commentaire
        })

# Affichage et suppression
if st.session_state.taches:
    st.subheader("📋 Liste des points")
    df = pd.DataFrame(st.session_state.taches)
    for i in range(len(df)):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"{i+1}. **{df.iloc[i]['Type']}** – {df.iloc[i]['Adresse']} – {df.iloc[i]['Heure']} – Priorité {df.iloc[i]['Priorité']}")
        with col2:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.taches.pop(i)
                st.experimental_rerun()
else:
    st.info("Ajoute au moins une adresse pour commencer.")

# Fonction de géocodage
@st.cache_data
def geocode_adresses(adresses):
    geolocator = Nominatim(user_agent="dispatch_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    coords = []
    for adresse in adresses:
        location = geocode(adresse)
        if location:
            coords.append((location.latitude, location.longitude))
    return coords

# Carte
if st.button("🗺️ Optimiser et afficher la tournée") and st.session_state.taches:
    with st.spinner("Géocodage des adresses..."):
        adresses = [t["Adresse"] for t in st.session_state.taches]
        coords = geocode_adresses(adresses)

    if len(coords) < 2:
        st.warning("Il faut au moins deux adresses valides.")
    else:
        st.subheader("🗺️ Carte de la tournée")
        carte = folium.Map(location=coords[0], zoom_start=6)
        for i, (lat, lon) in enumerate(coords):
            folium.Marker(
                [lat, lon],
                popup=f"{i+1}. {st.session_state.taches[i]['Type']} - {st.session_state.taches[i]['Adresse']}",
                tooltip=f"Étape {i+1}",
                icon=folium.Icon(color="blue" if st.session_state.taches[i]["Type"] == "Collecte" else "green")
            ).add_to(carte)
        folium.PolyLine(coords, color="red", weight=3).add_to(carte)
        st_folium(carte, width=700, height=500)
