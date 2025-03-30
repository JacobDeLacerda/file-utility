import streamlit as st
import shutil

# --- Configuration ---
# Match the cipher used in the tool page
ENCRYPTION_CIPHER = "aes-256-cbc"
OPENSSL_COMMAND = "openssl"

# --- Helper Functions ---
def check_openssl():
    """Checks if the openssl command is available in the system PATH."""
    return shutil.which(OPENSSL_COMMAND) is not None

# --- Page Configuration (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="Crypto Tool Home",
    page_icon="🏠",
    layout="centered" # "wide" or "centered"
)

# --- Landing Page Content ---
st.title("🔒 Welcome to the OpenSSL Crypto Tool")
st.image("https://user-images.githubusercontent.com/7419922/210158419-0c385606-175e-4622-8633-a765b5b44674.png", width=150) # Example image

st.markdown("---")

st.header("About This Tool")
st.markdown(f"""
This application provides a user-friendly interface for encrypting and decrypting files
using the robust **OpenSSL** library.

It utilizes the `{ENCRYPTION_CIPHER}` cipher with **PBKDF2** key derivation for enhanced security.
This means passwords are cryptographically stretched, making them harder to brute-force.

**Key Features:**
*   Easy file selection via browsing or drag-and-drop.
*   Encryption and Decryption modes.
*   Preview functionality for both input and output files (where possible).
*   Secure password handling within the browser (password is not stored long-term).
*   Downloadable encrypted/decrypted files.

**Disclaimer:**
*   Ensure you are using this tool responsibly and ethically.
*   **Crucially, remember your password!** There is no way to recover a file if the password is lost.
*   Compatibility is highest for files encrypted and decrypted using this tool or the exact same OpenSSL command-line parameters (`{ENCRYPTION_CIPHER}` with `-pbkdf2`).
*   While this tool aims to be secure, passing passwords directly to subprocesses has inherent risks compared to truly interactive prompts. Use in trusted environments.
""")

st.markdown("---")

# Check for OpenSSL and display status
st.subheader("System Check")
if check_openssl():
    st.success(f"✅ OpenSSL command ('{OPENSSL_COMMAND}') found!")
    st.info("Navigate to the **Encrypt Decrypt Tool** page using the sidebar on the left to begin.")
else:
    st.error(f"❌ Critical Error: '{OPENSSL_COMMAND}' command not found.")
    st.markdown(f"""
        Please ensure OpenSSL is installed on the system running this Streamlit app
        and that the `{OPENSSL_COMMAND}` executable is accessible in the system's PATH.

        You might need to install it using your system's package manager (e.g., `apt`, `yum`, `brew`)
        or download it from the official OpenSSL website.
    """)
    st.stop() # Stop execution if openssl is not found


st.markdown("---")
st.markdown("Developed with Streamlit and OpenSSL.")

# You can add more instructions or details here
