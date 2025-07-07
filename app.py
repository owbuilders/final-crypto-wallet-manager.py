import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io, base64, requests
from fpdf import FPDF
import os
import tempfile

# Set your password here
APP_PASSWORD = "mywallets"

# Logo caching directory
LOGO_DIR = "/mnt/data/coin_logos"
os.makedirs(LOGO_DIR, exist_ok=True)

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

# Function to generate QR code
def generate_qr(wallet_address):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(wallet_address)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    return img

# Function to download and cache coin logo
def fetch_logo(coin_name):
    filename = f"{coin_name.lower().replace(' ', '_')}.png"
    path = os.path.join(LOGO_DIR, filename)
    if not os.path.exists(path):
        url = f"https://cryptoicons.org/api/icon/{coin_name.lower()}/200"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
        except Exception:
            pass
    return path if os.path.exists(path) else None

# Mobile-friendly layout tweaks
st.markdown("""
    <style>
        .block-container {
            padding: 1rem 1rem 2rem;
            max-width: 700px;
            margin: auto;
        }
        h1, h2, h4, p {
            word-wrap: break-word;
        }
        @media only screen and (max-width: 600px) {
            img {
                width: 100% !important;
                height: auto !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# App title
st.markdown("<h1 style='font-size:22px;text-align:center;'>Crypto Wallet Manager</h1>", unsafe_allow_html=True)

# Upload CSV
uploaded_file = st.file_uploader("Upload your wallet CSV", type="csv")

# Prepare to build PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

if uploaded_file:
    st.success("✅ File uploaded!")
    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip()
    df['Wallet Name'] = df['Wallet Name'].astype(str).str.strip()
    df['Wallet Address'] = df['Wallet Address'].astype(str).str.strip()
    df['Coin Name'] = df['Coin Name'].astype(str).str.strip().str.lower()

    selected_wallet = st.selectbox("Select Wallet Name", ['All'] + sorted(df['Wallet Name'].unique()))

    filtered_df = df[df['Wallet Name'] == selected_wallet] if selected_wallet != 'All' else df

    if 'Wallet Type' in filtered_df.columns:
        grouped = filtered_df.groupby('Wallet Type')

        for wallet_type, group in grouped:
            group = group.sort_values(by='Wallet Name')

            st.markdown(f"""
            <div style='background-color:#e8f4fd;padding:10px 14px;border-radius:10px;margin-top:20px;margin-bottom:10px;'>
                <h2 style='margin:0;color:#2c3e50;font-size:18px;'>{wallet_type}</h2>
            </div>
            """, unsafe_allow_html=True)

            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=wallet_type, ln=True, align='C')

            for _, row in group.iterrows():
                wallet_name = row['Wallet Name']
                wallet_address = row['Wallet Address']
                coin_name = row['Coin Name']

                img = generate_qr(wallet_address)
                logo_path = fetch_logo(coin_name)

                # Display in app
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                data = base64.b64encode(buf.getvalue()).decode("utf-8")
                qr_tag = f"<img src='data:image/png;base64,{data}' style='width:100%;max-width:200px;margin:10px;'/>"

                logo_tag = ""
                if logo_path:
                    with open(logo_path, "rb") as f:
                        logo_data = base64.b64encode(f.read()).decode("utf-8")
                        logo_tag = f"<img src='data:image/png;base64,{logo_data}' style='height:40px;margin-left:10px;'/>"

                st.markdown(f"""
                <div style='border:1px solid #ccc;border-radius:10px;padding:12px;margin-bottom:16px;background-color:#f9f9f9;'>
                    <h4 style='margin:0;color:#34495e;font-size:16px;'>{wallet_name} ({coin_name.upper()}) {logo_tag}</h4>
                    <p style='margin:6px 0 8px 0;color:#555;font-size:14px;'><strong>Address:</strong> {wallet_address}</p>
                    {qr_tag}
                </div>
                """, unsafe_allow_html=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    img.save(tmpfile.name)
                try:
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(200, 10, txt=f"{wallet_name} ({coin_name.upper()})", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 8, f"Address: {wallet_address}")
                    pdf.image(tmpfile.name, x=10, w=50)
                    pdf.ln(10)
                finally:
                    os.remove(tmpfile.name)

        # Create downloadable PDF
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        st.download_button(
            label="📄 Download Wallets PDF",
            data=pdf_output.getvalue(),
            file_name="crypto_wallets.pdf",
            mime="application/pdf"
        )

    else:
        st.error("CSV file must have a column named 'Wallet Type'.")
else:
    st.info("Please upload a CSV file to begin.")

 
 
 
