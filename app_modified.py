import streamlit as st
import pandas as pd
import requests
import json
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Saisie Factures Auto", layout="centered")

st.title("📥 Saisie automatique des factures PDF avec OCR")
st.markdown("Charge une facture PDF, extrait les données clés grâce à l'API Mindee, valide et exporte en écriture comptable Excel.")

# Récupérer la clé API de Mindee (déjà intégrée)
api_key = 'ad96a927d1867171fdd99f520ee2bd97'  # Ta clé API Mindee

# Upload du fichier
uploaded_file = st.file_uploader("Dépose ta facture PDF ici", type="pdf")

def ocr_mindee(pdf_file):
    url = "https://api.mindee.net/v1/products/receipt/v1/predict"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    files = {
        'file': pdf_file
    }
    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json()  # Retourne le résultat OCR
    else:
        # Affichage détaillé de l'erreur avec texte complet
        st.error(f"Erreur d'OCR avec l'API Mindee. Code HTTP: {response.status_code}")
        st.error(f"Message d'erreur: {response.text}")
        return None

if uploaded_file:
    data = ocr_mindee(uploaded_file)

    if data:
        # Extraction des informations nécessaires du JSON renvoyé par Mindee
        fournisseur = data.get('document', {}).get('fields', {}).get('supplier_name', {}).get('value', 'Inconnu')
        date_facture = data.get('document', {}).get('fields', {}).get('date', {}).get('value', '01/01/2024')
        montant_ttc = data.get('document', {}).get('fields', {}).get('total_amount', {}).get('value', '0.00')

        # Affichage des informations extraites
        st.markdown("### 🧾 Informations extraites")

        st.write(f"**Fournisseur** : {fournisseur}")
        st.write(f"**Date facture** : {date_facture}")
        st.write(f"**Montant TTC** : {montant_ttc} €")

        # Transformations pour l'écriture comptable
        montant_ttc = float(montant_ttc)
        tva = 20  # Valeur par défaut
        montant_ht = round(montant_ttc / (1 + tva / 100), 2)
        montant_tva = round(montant_ttc - montant_ht, 2)

        # Création du tableau d'écriture comptable
        df = pd.DataFrame([
            {"Date": date_facture, "Journal": "ACHATS", "Compte": "606000", "Libellé": fournisseur, "Débit": montant_ht, "Crédit": 0},
            {"Date": date_facture, "Journal": "ACHATS", "Compte": "445660", "Libellé": "TVA " + fournisseur, "Débit": montant_tva, "Crédit": 0},
            {"Date": date_facture, "Journal": "ACHATS", "Compte": "401000", "Libellé": fournisseur, "Débit": 0, "Crédit": montant_ttc},
        ])

        st.markdown("### 💡 Aperçu écriture comptable")
        st.dataframe(df)

        # Export en Excel
        to_excel = BytesIO()
        with pd.ExcelWriter(to_excel, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Ecriture")
        to_excel.seek(0)

        st.download_button(
            label="📤 Télécharger l'écriture en Excel",
            data=to_excel,
            file_name="ecriture_comptable.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
