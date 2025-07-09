import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io, base64
from fpdf import FPDF
import os
import tempfile
import requests

APP_PASSWORD = "mywallets"

# Password protection
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    password = st.text_input("Enter password to access the wallet manager", type="password")
    if password == APP_PASSWORD:
        st.session_state.unlocked = True
        st.rerun()
    elif password != "":
        st.error("Incorrect password.")
    st.stop()

# QR code generator
def generate_qr(wallet_address):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
    qr.add_data(wallet_address)
    qr.make(fit=True)
    return qr.make_image(fill_color='black', back_color='white')

# PDF initialization
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# Layout tweaks
st.markdown("""
    <style>
        .block-container { padding: 1rem 1rem 2rem; max-width: 700px; margin: auto; }
        h1, h2, h4, p { word-wrap: break-word; }
        @media only screen and (max-width: 600px) {
            img { width: 100% !important; height: auto !important; }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='font-size:22px;text-align:center;'>Crypto Wallet Manager</h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your wallet CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Standardize columns
    df['Wallet Name'] = df['Wallet Name'].astype(str).str.strip()
    df['Coin Name'] = df['Coin Name'].astype(str).str.strip().str.lower()
    df['Coin Symbol'] = df['Coin Symbol'].astype(str).str.strip().str.upper()
    df['Coin Logo'] = df['Coin Logo'].astype(str).str.strip()
    df['Wallet Address'] = df['Wallet Address'].astype(str).str.strip()

    wallet_names = df['Wallet Name'].unique().tolist()
    selected_wallet = st.selectbox("Select Wallet", ["All"] + wallet_names)

    filtered_df = df if selected_wallet == "All" else df[df["Wallet Name"] == selected_wallet]

    coin_names = filtered_df['Coin Name'].unique().tolist()
    selected_coin = st.selectbox("Select Coin", ["All"] + coin_names)

    if selected_coin != "All":
        filtered_df = filtered_df[filtered_df['Coin Name'] == selected_coin.lower()]

    if not filtered_df.empty:
        grouped = filtered_df.groupby('Wallet Name')

        for wallet_name, group in grouped:
            st.markdown(f"<h2 style='color:#2c3e50;font-size:18px;'>{wallet_name}</h2>", unsafe_allow_html=True)
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=wallet_name, ln=True, align='C')

            for _, row in group.iterrows():
                coin_name = row['Coin Name']
                coin_symbol = row['Coin Symbol']
                coin_logo_url = row['Coin Logo']
                wallet_address = row['Wallet Address']

                # Show QR in app
                qr_img = generate_qr(wallet_address)
                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                data = base64.b64encode(buf.getvalue()).decode("utf-8")

                # Download logo
                try:
                    logo_response = requests.get(coin_logo_url)
                    logo_img = Image.open(io.BytesIO(logo_response.content)).resize((30, 30))
                    logo_buf = io.BytesIO()
                    logo_img.save(logo_buf, format="PNG")
                    logo_data = base64.b64encode(logo_buf.getvalue()).decode("utf-8")
                    logo_tag = f"<img src='data:image/png;base64,{logo_data}' width='30' height='30' style='vertical-align:middle;margin-right:10px;'/>"
                except:
                    logo_tag = "(unknown logo)"

                # Display in app
                st.markdown(f"""
                <div style='border:1px solid #ccc;border-radius:10px;padding:12px;margin-bottom:16px;background-color:#f9f9f9;'>
                    <h4 style='margin:0;color:#34495e;font-size:16px;'>{logo_tag}{coin_symbol}</h4>
                    <p style='margin:6px 0 8px 0;color:#555;font-size:14px;'><strong>Address:</strong> {wallet_address}</p>
                    <img src='data:image/png;base64,{data}' style='width:100%;max-width:300px;margin:10px auto;display:block;'/>
                </div>
                """, unsafe_allow_html=True)

                # Add to PDF
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(200, 10, txt=coin_symbol, ln=True)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 8, f"Address: {wallet_address}")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    qr_img.save(tmpfile.name)
                    pdf.image(tmpfile.name, x=10, w=40)
                    os.unlink(tmpfile.name)

    # Save PDF
    pdf_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(pdf_output.name)

    with open(pdf_output.name, "rb") as f:
        st.download_button("📄 Download Wallets PDF", data=f, file_name="crypto_wallets.pdf", mime="application/pdf")
        os.unlink(pdf_output.name)

else:
    st.info("Please upload a CSV file to begin.")

 
 
 
