import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io, base64, requests
from fpdf import FPDF
import os
import tempfile

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

# Generate QR code
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

# Fetch coin logo
def get_coin_logo(coin_name):
    coin_name = coin_name.lower()
    url = f"https://cryptoicons.org/api/icon/{coin_name}/64"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
    return None

# Mobile-friendly layout
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

st.markdown("<h1 style='font-size:22px;text-align:center;'>Crypto Wallet Manager</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your wallet CSV", type="csv")

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

if uploaded_file:
    st.success("✅ File uploaded!")
    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip()
    df['Wallet Name'] = df['Wallet Name'].astype(str).str.strip()
    df['Wallet Address'] = df['Wallet Address'].astype(str).str.strip()
    df['Coin Name'] = df['Coin Name'].astype(str).str.strip().str.lower()

    if 'Wallet Type' in df.columns:
        grouped = df.groupby('Wallet Type')

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

                # Generate QR
                img = generate_qr(wallet_address)

                # Fetch logo
                logo_img = get_coin_logo(coin_name)
                logo_data_uri = ""
                if logo_img:
                    logo_buf = io.BytesIO()
                    logo_img.save(logo_buf, format="PNG")
                    logo_data = base64.b64encode(logo_buf.getvalue()).decode("utf-8")
                    logo_data_uri = f"<img src='data:image/png;base64,{logo_data}' width='24' style='vertical-align:middle;margin-right:8px;'/>"

                # Display in Streamlit
                qr_buf = io.BytesIO()
                img.save(qr_buf, format="PNG")
                qr_data = base64.b64encode(qr_buf.getvalue()).decode("utf-8")

                st.markdown(f"""
                <div style='border:1px solid #ccc;border-radius:10px;padding:12px;margin-bottom:16px;background-color:#f9f9f9;'>
                    <h4 style='margin:0;color:#34495e;font-size:16px;'>{logo_data_uri}{wallet_name}</h4>
                    <p style='margin:6px 0 8px 0;color:#555;font-size:14px;'><strong>Address:</strong> {wallet_address}</p>
                    <img src='data:image/png;base64,{qr_data}' style='width:100%;max-width:300px;margin:10px auto;display:block;'/>
                </div>
                """, unsafe_allow_html=True)

                # Save temp QR
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    img.save(tmpfile.name)
                    temp_path = tmpfile.name

                # PDF: Coin logo
                if logo_img:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as logo_file:
                        logo_img.save(logo_file.name)
                        logo_path = logo_file.name
                    pdf.image(logo_path, x=10, y=pdf.get_y(), w=10)
                    os.remove(logo_path)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f" {wallet_name}", ln=True)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 8, f"Address: {wallet_address}")
                pdf.image(temp_path, x=10, w=50)
                pdf.ln(10)
                os.remove(temp_path)

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        st.download_button(
            label="📄 Download Wallets PDF",
            data=pdf_output.getvalue(),
            file_name="crypto_wallets_with_logos.pdf",
            mime="application/pdf"
        )
    else:
        st.error("CSV file must have a column named 'Wallet Type'.")
else:
    st.info("Please upload a CSV file to begin.")

 
 
 
