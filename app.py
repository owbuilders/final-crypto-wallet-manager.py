import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io, base64
from fpdf import FPDF
import os
import tempfile

APP_PASSWORD = "mywallets"

# --- Password Protection ---
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

# --- QR Code Generator ---
def generate_qr(wallet_address):
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10, border=2,
    )
    qr.add_data(wallet_address)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    return img

# --- Style (Mobile Friendly) ---
st.markdown("""
    <style>
        .block-container { padding: 1rem 1rem 2rem; max-width: 700px; margin: auto; }
        h1, h2, h4, p { word-wrap: break-word; }
        @media only screen and (max-width: 600px) {
            img { width: 100% !important; height: auto !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 style='font-size:22px;text-align:center;'>Crypto Wallet Manager</h1>", unsafe_allow_html=True)

# --- Try loading local CSV as default ---
try:
    default_df = pd.read_csv("cleaned_wallets.csv")
except FileNotFoundError:
    default_df = None


# --- CSV Upload ---
uploaded_file = st.file_uploader("Upload your wallet CSV (optional)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = default_df

# --- Main Display Logic ---
if df is not None:
    st.success("✅ Wallet data loaded!")

    df.columns = df.columns.str.strip()
    df['Wallet Name'] = df['Wallet Name'].astype(str).str.strip()
    df['Wallet Address'] = df['Wallet Address'].astype(str).str.strip()

    wallet_names = df['Wallet Name'].unique().tolist()
    selected_wallet = st.selectbox("Select Wallet Name", ["All"] + wallet_names)

    filtered_df = df if selected_wallet == "All" else df[df['Wallet Name'] == selected_wallet]

    coin_names = filtered_df['Coin Name'].unique().tolist() if 'Coin Name' in df.columns else []
    selected_coin = st.selectbox("Select Coin Name", ["All"] + coin_names) if coin_names else "All"

    if selected_coin != "All":
        filtered_df = filtered_df[filtered_df['Coin Name'] == selected_coin]

    # --- PDF setup ---
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Crypto Wallets", ln=True, align='C')

    # --- Loop through rows ---
    for _, row in filtered_df.iterrows():
        wallet_name = row.get('Wallet Name', '')
        wallet_address = row.get('Wallet Address', '')
        coin_logo = row.get('Logo URL', '')
        coin_name = row.get('Coin Name', '')
        coin_symbol = row.get('Coin Symbol', '')

        img = generate_qr(wallet_address)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = base64.b64encode(buf.getvalue()).decode("utf-8")
        img_tag = f"<img src='data:image/png;base64,{data}' style='width:100%;max-width:300px;margin:10px auto;display:block;'/>"

        # --- Coin logo if exists ---
        if isinstance(coin_logo, str) and coin_logo.strip() != "":
            st.image(coin_logo, width=40)

        st.markdown(f"""
        <div style='border:1px solid #ccc;border-radius:10px;padding:12px;margin-bottom:16px;background-color:#f9f9f9;'>
            <h4 style='margin:0;color:#34495e;font-size:16px;'>{wallet_name}</h4>
            <p style='margin:4px 0 6px 0;color:#555;font-size:14px;'><strong>Coin:</strong> {coin_name} ({coin_symbol})</p>
            <p style='margin:4px 0 6px 0;color:#555;font-size:14px;'><strong>Address:</strong> {wallet_address}</p>
            {img_tag}
        </div>
        """, unsafe_allow_html=True)

        # Add to PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            temp_path = tmpfile.name
            img.save(temp_path)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=wallet_name, ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 8, f"{coin_name} ({coin_symbol})\nAddress: {wallet_address}")
        pdf.image(temp_path, x=10, w=50)
        pdf.ln(10)
        os.remove(temp_path)

    # --- PDF Download ---
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    st.download_button(
        label="📄 Download Wallets PDF",
        data=pdf_output.getvalue(),
        file_name="crypto_wallets.pdf",
        mime="application/pdf"
    )

else:
    st.warning("Please upload a CSV file or place 'cleaned_wallets.csv' in this folder.")

 
 
 
