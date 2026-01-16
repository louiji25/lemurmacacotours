import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime, date
import qrcode

# ==========================================
# 1. CONFIGURATION & TARIFS
# ==========================================
st.set_page_config(page_title="LMT Billing System - A4", layout="wide")
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
# 2. MOTEUR PDF FORMAT A4
# ==========================================
class PDF_A4(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", x=90, y=10, w=30) # Centré sur A4
            self.ln(25)
        self.set_font("Helvetica", 'B', 16)
        self.cell(0, 10, "LEMUR MACACO TOURS SARL", ln=True, align='C')
        self.set_font("Helvetica", '', 9)
        self.cell(0, 5, "NIF: 4019433197 | STAT: 79120 71 2025 0 10965", ln=True, align='C')
        self.cell(0, 5, "Andrekareka - Hell Ville - Nosy Be | Madagascar", ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-40)
        self.set_font("Helvetica", 'B', 10)
        self.set_x(50)
        self.cell(0, 6, "COORDONNEES BANCAIRES", ln=True)
        self.set_font("Helvetica", '', 9)
        self.set_x(50)
        self.cell(0, 5, "BMOI - RIB : MG46 0000 4000 2605 8277 2010 129", ln=True)
        self.set_x(50)
        self.cell(0, 5, "SWIFT : BMOIMGMG", ln=True)

def generate_invoice_a4(data):
    pdf = PDF_A4(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # En-tête Facture
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"FACTURE : {data['ref']}", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 7, f"Date de facture : {data['date']}", ln=True)
    pdf.cell(0, 7, f"Client : {data['client'].upper()}", ln=True)
    pdf.cell(0, 7, f"Nombre de Pax : {data['pax']} | Jours : {data['jours']}", ln=True)
    
    d_deb = data['d_deb'].strftime("%d-%m-%Y")
    d_fin = data['d_fin'].strftime("%d-%m-%Y")
    pdf.set_font("Helvetica", 'I', 11)
    pdf.cell(0, 7, f"Réservation : du {d_deb} au {d_fin}", ln=True)
    pdf.ln(5)

    # TABLEAU - Structure regroupée
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(120, 10, " Description", border=1, fill=True)
    pdf.cell(30, 10, "Nombre", border=1, fill=True, align='C')
    pdf.cell(40, 10, "Montant (Ar)", border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font("Helvetica", '', 10)
    
    # --- Bloc SITES REGROUPÉS ---
    sites_sel = [i for i in data['items'] if "Entree" in i[0]]
    if sites_sel:
        noms_sites = "-".join([i[0].replace("Entree ", "") for i in sites_sel])
        pdf.set_font("Helvetica", 'B', 10)
        start_y = pdf.get_y()
        pdf.multi_cell(120, 8, f"Sites : {noms_sites}", border='LTB')
        end_y = pdf.get_y()
        h = end_y - start_y
        pdf.set_xy(130, start_y)
        pdf.cell(30, h, str(len(sites_sel)), border=1, align='C')
        pdf.cell(40, h, f"{sum(i[2] for i in sites_sel):,.0f}", border=1, align='R')
        pdf.set_xy(10, end_y)

    # --- Bloc GUIDES REGROUPÉS ---
    guides_sel = [i for i in data['items'] if "Guide local" in i[0]]
    if guides_sel:
        noms_guides = "-".join([i[0].replace("Guide local ", "") for i in guides_sel])
        pdf.set_font("Helvetica", 'B', 10)
        start_y = pdf.get_y()
        pdf.multi_cell(120, 8, f"Guides : {noms_guides}", border='LTB')
        end_y = pdf.get_y()
        h = end_y - start_y
        pdf.set_xy(130, start_y)
        pdf.cell(30, h, str(len(guides_sel)), border=1, align='C')
        pdf.cell(40, h, f"{sum(i[2] for i in guides_sel):,.0f}", border=1, align='R')
        pdf.set_xy(10, end_y)

    # --- Autres services (Logistique) ---
    pdf.set_font("Helvetica", '', 10)
    autres = [i for i in data['items'] if "Entree" not in i[0] and "Guide local" not in i[0]]
    for desc, nb, mt in autres:
        pdf.cell(120, 10, f" {desc}", border=1)
        pdf.cell(30, 10, str(nb), border=1, align='C')
        pdf.cell(40, 10, f"{mt:,.0f}", border=1, align='R')
        pdf.ln()

    # --- TOTAUX ---
    total_final = data['total_ar'] * (1 + data['marge'] / 100)
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(150, 10, "TOTAL NET ", align='R')
    pdf.cell(40, 10, f"{total_final:,.0f} Ar", border=1, align='R')
    pdf.ln()
    pdf.set_text_color(0, 0, 255) # Bleu pour l'euro
    pdf.cell(150, 10, "EQUIVALENT EURO ", align='R')
    pdf.cell(40, 10, f"{total_final/TAUX_AR_TO_EUR:,.2f} EUR", border=1, align='R')
    pdf.set_text_color(0, 0, 0)

    # QR Code dynamique en bas à gauche sur A4
    qr_content = f"LMT-Facture: {data['ref']}\nTotal: {total_final:,.0f} Ar"
    qr = qrcode.make(qr_content)
    qr_path = "temp_qr.png"
    qr.save(qr_path)
    pdf.image(qr_path, 10, 250, 30, 30) 

    return bytes(pdf.output())

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================
st.title("📂 LMT - Facturation Professionnelle A4")

with st.sidebar:
    st.header("👤 Client & Dates")
    nom_client = st.text_input("Nom du Client")
    col_d1, col_d2 = st.columns(2)
    d_deb = col_d1.date_input("Du", value=date.today())
    d_fin = col_d2.date_input("Au", value=date.today())
    pax = st.number_input("Nombre de Pax", min_value=1, value=2)
    jours = st.number_input("Nombre de Jours", min_value=1, value=1)
    marge = st.slider("Marge bénéficiaire (%)", 0, 100, 20)

circuit_sel = st.selectbox("📍 Sélectionner le Circuit", list(TARIFS.keys()))
data_c = TARIFS[circuit_sel]

# Sélections
col1, col2, col3 = st.columns(3)
items_facture = []
total_brut = 0

with col1:
    st.subheader("🏞️ Sites")
    for s, p in data_c["entrees"].items():
        if st.checkbox(s):
            items_facture.append((f"Entree {s}", pax, p * pax))
            total_brut += p * pax
    if st.checkbox("Restaurant", value=True):
        m_r = data_c["restau_pax_jour"] * pax * jours
        items_facture.append(("Restaurant", 1, m_r))
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
    if st.checkbox("Porteur"):
        nb_p = st.number_input("Nb Porteurs", min_value=1, value=1)
        m_p = data_c["porteur_par_j_pers"] * nb_p * jours
        items_facture.append((f"Porteur", nb_p, m_p))
        total_brut += m_p
    if st.checkbox("Carburant"):
        items_facture.append(("Carburant", 1, data_c["fixes"]["Carburant"]))
        total_brut += data_c["fixes"]["Carburant"]

st.divider()
total_avec_marge = total_brut * (1 + marge / 100)
c1, c2, c3 = st.columns(3)
c1.metric("Total Brut", f"{total_brut:,.0f} Ar")
c2.metric("TOTAL NET", f"{total_avec_marge:,.0f} Ar")
c3.metric("EURO", f"{total_avec_marge/TAUX_AR_TO_EUR:,.2f} €")

if st.button("💾 GÉNÉRER LA FACTURE A4"):
    if not nom_client:
        st.error("Nom du client requis.")
    else:
        doc_data = {
            "ref": f"LMT-{datetime.now().strftime('%y%m%d%H%M')}",
            "date": datetime.now().strftime("%d/%m/%Y"),
            "client": nom_client, "pax": pax, "jours": jours,
            "d_deb": d_deb, "d_fin": d_fin,
            "items": items_facture, "total_ar": total_brut, "marge": marge
        }
        pdf_bytes = generate_invoice_a4(doc_data)
        st.download_button("📥 Télécharger PDF A4", pdf_bytes, f"Facture_{nom_client}_A4.pdf")
