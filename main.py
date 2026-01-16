import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime, date
import qrcode
from io import BytesIO

# ==========================================
# 1. CONFIGURATION & TARIFS (Basé sur vos images)
# ==========================================
st.set_page_config(page_title="LMT Billing System", layout="wide")
TAUX_AR_TO_EUR = 5000 

TARIFS = {
    "Circuit Nord-Ouest": {
        "entrees": {
            "Montagne des Français": 30000, "Trois Baies": 10000, 
            "Montagne d'Ambre": 55000, "Tsingy Rouge": 35000, 
            "Ankaragna": 65000, "Agnivorano": 140000
        },
        "guides_site": {
            "Montagne des Français": 50000, "Trois Baies": 100000,
            "Montagne d'Ambre": 100000, "Tsingy Rouge": 100000,
            "Ankaragna": 120000, "Agnivorano": 100000
        },
        "services_jour": {
            "Location Voiture": 200000, "Guide accompagnateur": 150000, 
            "Chauffeur": 30000, "Cuisinier": 50000
        },
        "fixes": {"Carburant": 500000},
        "restau_pax_jour": 40000,
        "porteur_par_j_pers": 20000 
    },
    "Circuit Nord-Est": {
        "entrees": {"Andapa (Marojejy)": 140000},
        "guides_site": {
            "Daraina": 100000, "Vohemar": 100000, "Andapa (Marojejy)": 100000,
            "Antalaha": 100000, "Sambava": 100000
        },
        "services_jour": {
            "Location Voiture": 300000, "Guide accompagnateur": 150000, 
            "Chauffeur": 40000, "Cuisinier": 60000
        },
        "fixes": {"Carburant": 1200000},
        "restau_pax_jour": 40000,
        "porteur_par_j_pers": 25000
    }
}

# ==========================================
# 2. CLASSE PDF PERSONNALISÉE (A5)
# ==========================================
class PDF_A5(FPDF):
    def header(self):
        # Logo centré au-dessus du nom
        if os.path.exists("logo.png"):
            self.image("logo.png", x=59, y=8, w=30)
            self.ln(25)
        else:
            self.ln(5)
            
        self.set_font("Helvetica", 'B', 14)
        self.cell(0, 8, "LEMUR MACACO TOURS SARL", ln=True, align='C')
        self.set_font("Helvetica", '', 8)
        self.cell(0, 4, "NIF: 4019433197 | STAT: 79120 71 2025 0 10965", ln=True, align='C')
        self.cell(0, 4, "Andrekareka - Hell Ville - Nosy Be | Madagascar", ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-35)
        self.set_font("Helvetica", 'B', 8)
        self.set_x(40) 
        self.cell(0, 5, "COORDONNEES BANCAIRES", ln=True)
        self.set_font("Helvetica", '', 7)
        self.set_x(40)
        self.cell(0, 4, "BMOI - RIB : MG46 0000 4000 2605 8277 2010 129", ln=True)
        self.set_x(40)
        self.cell(0, 4, "SWIFT : BMOIMGMG", ln=True)

def generate_invoice_a5(data):
    pdf = PDF_A5(format='A5')
    pdf.add_page()
    
    # Infos En-tête
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 8, f"FACTURE : {data['ref']}", ln=True)
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(0, 5, f"Date de facture : {data['date']}", ln=True)
    pdf.cell(0, 5, f"Nombre de Pax : {data['pax']} | Jours : {data['jours']}", ln=True)
    
    d_deb = data['d_deb'].strftime("%d-%m-%Y")
    d_fin = data['d_fin'].strftime("%d-%m-%Y")
    pdf.set_font("Helvetica", 'I', 9)
    pdf.cell(0, 5, f"Réservation : du {d_deb} au {d_fin}", ln=True)
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(0, 5, f"Client : {data['client'].upper()}", ln=True)
    pdf.ln(4)

    # Tableau des prestations
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.cell(85, 8, " Description", border=1, fill=True)
    pdf.cell(15, 8, "Nombre", border=1, fill=True, align='C')
    pdf.cell(28, 8, "Montant", border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font("Helvetica", '', 7)
    for desc, nb, mt in data['items']:
        pdf.cell(85, 6, f" {desc}", border=1)
        pdf.cell(15, 6, str(nb), border=1, align='C')
        pdf.cell(28, 6, f"{mt:,.0f}", border=1, align='R')
        pdf.ln()

    # Totaux
    total_final = data['total_ar'] * (1 + data['marge'] / 100)
    pdf.ln(3)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(100, 7, "TOTAL NET", align='R')
    pdf.cell(28, 7, f"{total_final:,.0f} Ar", border=1, align='R')
    
    # Equivalent Euro en bleu
    pdf.ln()
    pdf.set_text_color(0, 0, 255) 
    pdf.cell(100, 7, "EQUIVALENT EURO", align='R')
    pdf.cell(28, 7, f"{total_final/TAUX_AR_TO_EUR:,.2f} EUR", border=1, align='R')
    pdf.set_text_color(0, 0, 0)

    # QR Code dynamique
    qr_content = f"LMT Facture: {data['ref']}\nClient: {data['client']}\nTotal: {total_final:,.0f} Ar"
    qr = qrcode.make(qr_content)
    qr_path = "temp_qr.png"
    qr.save(qr_path)
    pdf.image(qr_path, 10, 175, 25, 25) 
    
    return bytes(pdf.output())

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================
st.title("📂 Gestionnaire de Factures LMT")

with st.sidebar:
    st.header("👤 Information Client")
    nom_client = st.text_input("Nom du Client")
    
    # Dates côte à côte
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_debut = st.date_input("Du", value=date.today())
    with col_d2:
        d_fin = st.date_input("Au", value=date.today())
    
    pax = st.number_input("Nombre de Pax", min_value=1, value=2)
    jours = st.number_input("Nombre de Jours", min_value=1, value=1)
    marge = st.slider("Marge (%)", 0, 100, 20)

circuit_sel = st.selectbox("📍 Circuit", list(TARIFS.keys()))
data_c = TARIFS[circuit_sel]

col1, col2, col3 = st.columns(3)
items_facture = []
total_brut = 0

with col1:
    st.subheader("🏞️ Sites & Resto")
    for s, p in data_c["entrees"].items():
        if st.checkbox(s):
            items_facture.append((f"Entree {s}", pax, p * pax))
            total_brut += p * pax
    if st.checkbox("Restaurant", value=True):
        m_r = data_c["restau_pax_jour"] * pax * jours
        items_facture.append((f"Restaurant", 1, m_r))
        total_brut += m_r

with col2:
    st.subheader("👨‍🏫 Guides")
    for s, p in data_c["guides_site"].items():
        if st.checkbox(f"Guide {s}"):
            items_facture.append((f"Guide local {s}", 1, p))
            total_brut += p

with col3:
    st.subheader("🚗 Logistique")
    for s, p in data_c["services_jour"].items():
        if st.checkbox(s):
            items_facture.append((f"{s}", 1, p * jours))
            total_brut += p * jours
    
    # Option Porteur
    if st.checkbox("Porteur"):
        nb_p = st.number_input("Nombre de porteurs", min_value=1, value=1)
        m_p = data_c["porteur_par_j_pers"] * nb_p * jours
        items_facture.append((f"Porteur ({nb_p})", nb_p, m_p))
        total_brut += m_p
        
    if st.checkbox("Carburant"):
        items_facture.append(("Carburant", 1, data_c["fixes"]["Carburant"]))
        total_brut += data_c["fixes"]["Carburant"]

# Affichage des totaux sur l'interface
st.divider()
total_avec_marge = total_brut * (1 + marge / 100)

c_res1, c_res2, c_res3 = st.columns(3)
c_res1.metric("Total Brut", f"{total_brut:,.0f} Ar")
c_res2.metric("TOTAL NET", f"{total_avec_marge:,.0f} Ar")
c_res3.metric("EURO (€)", f"{total_avec_marge/TAUX_AR_TO_EUR:,.2f} €")

if st.button("🚀 GÉNÉRER LA FACTURE PDF"):
    if not nom_client:
        st.error("Veuillez saisir le nom du client.")
    else:
        doc_data = {
            "ref": f"LMT-{datetime.now().strftime('%y%m%d%H%M')}",
            "date": datetime.now().strftime("%d/%m/%Y"),
            "client": nom_client, "pax": pax, "jours": jours,
            "d_deb": d_debut, "d_fin": d_fin,
            "items": items_facture, "total_ar": total_brut, "marge": marge
        }
        pdf_output = generate_invoice_a5(doc_data)
        st.download_button("📥 Télécharger PDF", pdf_output, f"Facture_{nom_client}.pdf")
