# crypto_app.py (Main Landing Page)

import streamlit as st
import shutil

# --- Configuration ---
ENCRYPTION_CIPHER = "aes-256-cbc" # From Encrypt/Decrypt Tool
OPENSSL_COMMAND = "openssl"
ZIP_COMMAND = "zip" # From Zip Tool

# --- Helper Functions ---
def check_commands():
    """Checks if required commands (openssl, zip) are available."""
    missing = []
    if shutil.which(OPENSSL_COMMAND) is None:
        missing.append(OPENSSL_COMMAND)
    if shutil.which(ZIP_COMMAND) is None:
        missing.append(ZIP_COMMAND)
    return missing

# --- Page Configuration (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="Crypto App Home",
    page_icon="🛡️", # Changed icon to something more general/secure
    layout="centered"
)

# --- Landing Page Content ---

st.title("🛡️ Welcome to the Cryptography & File Utilities Application") # More general title

st.markdown("---")

st.header("About This App")
st.markdown(f"""
This application provides user-friendly tools for common file security and manipulation tasks,
leveraging standard command-line utilities like **OpenSSL** and **Zip**.

**Available Tools (Select from Sidebar):**

1.  **Encrypt Decrypt Tool:**
    *   Uses OpenSSL's `{ENCRYPTION_CIPHER}` cipher with PBKDF2 for strong file encryption/decryption.
    *   Ideal for securing individual files with a password.

2.  **Zip File Tool:**
    *   Creates password-protected ZIP archives using the system's `zip` command (`-e` flag).
    *   Suitable for bundling and protecting files with standard ZIP encryption. *(Note: Standard ZIP encryption is generally considered less secure than AES used in the Encrypt/Decrypt tool)*.

**General Features:**
*   Easy file selection via browsing or drag-and-drop.
*   Clear interface for performing operations.
*   Secure password handling within the browser session.
*   Downloadable output files.

**Important Considerations & Disclaimers:**
*   Ensure you are using these tools responsibly and ethically.
*   **Crucially, remember your passwords!** There is no way to recover a file if the password is lost for either encryption or ZIP protection.
*   Encryption compatibility is highest for files encrypted and decrypted using the Encrypt/Decrypt tool or the exact same OpenSSL parameters.
*   The ZIP tool relies on standard `zip` encryption, which may have compatibility variations and is less robust than modern AES encryption.
*   **Security Note:** For automation, both tools pass passwords non-interactively to their respective command-line utilities. This might expose the password temporarily in the system's process list. Use with caution in shared or untrusted environments.
""")

st.markdown("---")

# Check for Required Commands and display status
st.subheader("System Check")
missing_commands = check_commands()

if not missing_commands:
    st.success(f"✅ Required commands ('{OPENSSL_COMMAND}', '{ZIP_COMMAND}') found!")
    st.info("Navigate to the desired tool page using the sidebar on the left to begin.")
else:
    st.error(f"❌ Critical Error: The following command(s) were not found: `{'`, `'.join(missing_commands)}`")
    st.markdown(f"""
        Please ensure the missing command-line utilities are installed on the system running this Streamlit app
        and are accessible in the system's PATH.

        *   **OpenSSL:** Usually available on macOS/Linux. Install via package manager (`apt`, `yum`, `brew`) or from [OpenSSL website](https://www.openssl.org/).
        *   **Zip:** Usually available on macOS/Linux. Install via package manager if missing (e.g., `sudo apt install zip`, `sudo yum install zip`).

        The application may not function correctly until these are installed.
    """)
    # Allow navigation but show the error prominently
    # st.stop() # Removing stop so users can still see the app structure

st.markdown("---")
st.markdown("Developed with Streamlit.")
