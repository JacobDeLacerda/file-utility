# pages/2_Zip_File_Tool.py

import streamlit as st
import subprocess
import os
import tempfile
import shutil
import mimetypes # To guess file types for download

# --- Configuration ---
ZIP_COMMAND = "zip"

# --- Helper Functions ---

def check_zip_command():
    """Checks if the zip command is available in the system PATH."""
    if shutil.which(ZIP_COMMAND) is None:
        st.error(f"CRITICAL ERROR: '{ZIP_COMMAND}' command not found. Please ensure the native zip utility is installed and in the system PATH.")
        st.stop()
    return True

def run_zip_command(args, password_for_masking):
    """
    Runs the zip command with given arguments.
    Returns tuple: (success_boolean, stdout_str, stderr_str)
    """
    command = [ZIP_COMMAND] + args

    # --- SECURITY WARNING ---
    # We use the -P flag which puts the password on the command line.
    # This is less secure than an interactive prompt as the password
    # might be visible in process lists (e.g., `ps aux`) temporarily.
    # Mask the password for display purposes only.
    printable_command = []
    password_found = False
    for i, arg in enumerate(command):
        if arg == '-P' and i + 1 < len(command):
            printable_command.extend([arg, '********'])
            password_found = True
        elif password_found:
            password_found = False # Skip the actual password argument in the printable version
            continue
        else:
            printable_command.append(arg)
    #st.write(f"DEBUG: Running command: `{' '.join(printable_command)}`") # For debugging

    try:
        # Use a timeout to prevent hangs
        process = subprocess.run(
            command,
            check=False, # Don't raise exception on non-zero exit, check manually
            capture_output=True,
            text=True,
            timeout=120 # Increased timeout for potentially larger zips
        )
        success = process.returncode == 0

        # zip often returns code 12 for "nothing to do" which isn't necessarily a fatal error
        # but can happen if input doesn't match. We'll treat any non-zero as failure for simplicity here.
        if not success:
             # Try to provide a more specific common error message
            err_lower = process.stderr.lower()
            if "nothing to do" in err_lower:
                 st.error(f"Zip Error (Exit Code {process.returncode}): Nothing to zip. Check input file path.\n```\n{process.stderr.strip()}\n```")
            else:
                 st.error(f"Zip Error (Exit Code {process.returncode}):\n```\n{process.stderr.strip()}\n```")

        # Also print stderr if zip succeeded but printed warnings/info
        elif process.stderr:
             st.info(f"Zip Messages (stderr):\n```\n{process.stderr.strip()}\n```")

        return success, process.stdout.strip(), process.stderr.strip()

    except subprocess.TimeoutExpired:
        st.error("Zip command timed out after 120 seconds.")
        return False, "", "Timeout expired"
    except FileNotFoundError:
         st.error(f"Error: The '{ZIP_COMMAND}' command was not found. Is it installed and in PATH?")
         return False, "", f"Command not found: {ZIP_COMMAND}"
    except Exception as e:
        st.error(f"An unexpected error occurred while running zip: {e}")
        return False, "", str(e)

# --- Streamlit App ---

st.set_page_config(
    page_title="Zip Tool",
    page_icon="📦"
)

st.title("📦 Create Password-Protected ZIP File")
st.markdown("Uses the system's `zip` command with password protection.")

# --- Check zip command availability ---
check_zip_command()

# --- Session State Initialization ---
if 'output_zip_content' not in st.session_state:
    st.session_state.output_zip_content = None
if 'output_zip_filename' not in st.session_state:
    st.session_state.output_zip_filename = None
if 'zip_operation_status' not in st.session_state:
    st.session_state.zip_operation_status = None # Can be "success", "fail", or None

# --- UI Elements ---
st.info("**Note:** This tool currently supports zipping a single file.", icon="ℹ️")
uploaded_file = st.file_uploader("Choose the file to zip", type=None, key="zip_uploader")

# Password Input
st.markdown("### Set ZIP Password")
col1, col2 = st.columns(2)
with col1:
    password = st.text_input("Enter Password:", type="password", key="zip_pwd1")
with col2:
    password_confirm = st.text_input("Confirm Password:", type="password", key="zip_pwd2")

# Output Filename Suggestion/Input
default_output_filename = ""
if uploaded_file:
    input_base, _ = os.path.splitext(uploaded_file.name)
    default_output_filename = f"{input_base}_protected.zip"

output_filename_user = st.text_input(
    "Desired Output ZIP Filename:",
    value=default_output_filename,
    placeholder="e.g., protected_archive.zip"
)

# Action Button and Status Area
st.markdown("---")

# Security Warning about the method
st.warning("""
    **Security Note:** For automation, this tool passes the password directly to the `zip` command using the `-P` flag.
    This means the password might be temporarily visible in your system's process list.
    This is less secure than interactive password prompts used in the terminal. Use with caution in shared environments.
""", icon="⚠️")


run_button = st.button("Create Protected ZIP", type="primary", disabled=not uploaded_file)
status_placeholder = st.empty()
download_placeholder = st.empty()

# --- Logic Execution ---
if run_button and uploaded_file:
    # Reset previous results
    st.session_state.output_zip_content = None
    st.session_state.output_zip_filename = None
    st.session_state.zip_operation_status = None
    status_placeholder.info("Processing...")
    download_placeholder.empty()

    # --- Input Validation ---
    if not password:
        status_placeholder.error("Password cannot be empty.")
        st.stop()
    if password != password_confirm:
        status_placeholder.error("Passwords do not match.")
        st.stop()
    if not output_filename_user:
        status_placeholder.error("Output ZIP filename cannot be empty.")
        st.stop()
    if not output_filename_user.lower().endswith('.zip'):
        status_placeholder.warning("Output filename doesn't end with '.zip'. Adding it automatically.")
        output_filename_user += ".zip"


    # --- File Handling & Zip Execution ---
    temp_dir = None # Initialize for finally block
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        input_file_path = os.path.join(temp_dir, uploaded_file.name)
        output_file_path = os.path.join(temp_dir, output_filename_user)

        # Write uploaded content to the temporary input file
        with open(input_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Prepare Zip arguments
        # zip [options] [-P password] [zipfile] [list_of_files]
        # -j : Junk paths (store only the file, not directory structure) - good for single files
        args = [
            '-j', # Junk paths
            '-e', # Encrypt (standard encryption, less secure than AES used by 7zip/WinRAR)
                  # Alternatively, -P for direct password (often needed with -e non-interactively)
            '-P', password, # Provide password directly
            output_file_path, # Output zip file path
            input_file_path   # Input file path
        ]


        # Run the command
        success, stdout, stderr = run_zip_command(args, password)

        if success and os.path.exists(output_file_path):
            st.session_state.zip_operation_status = "success"
            # Read the output zip file content for download
            with open(output_file_path, "rb") as f:
                st.session_state.output_zip_content = f.read()
            st.session_state.output_zip_filename = output_filename_user # Store the intended filename

            status_placeholder.success("Password-protected ZIP created successfully!")

            # Add Download Button
            download_placeholder.download_button(
                label=f"Download {st.session_state.output_zip_filename}",
                data=st.session_state.output_zip_content,
                file_name=st.session_state.output_zip_filename,
                mime='application/zip' # Standard MIME type for zip
            )

        else:
            st.session_state.zip_operation_status = "fail"
            # Error message already displayed by run_zip_command
            status_placeholder.error("Failed to create ZIP file. See details above.")
             # Clean up potentially incomplete output file
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                except OSError:
                    pass # Ignore cleanup error

    except Exception as e:
        status_placeholder.error(f"An error occurred during ZIP processing: {e}")
        st.session_state.zip_operation_status = "fail"
    finally:
        # --- Cleanup ---
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                # st.write(f"DEBUG: Cleaned up temp directory: {temp_dir}") # For debugging
            except Exception as e:
                st.warning(f"Could not automatically clean up temporary directory {temp_dir}: {e}")

# --- Display previous successful results if no new file is uploaded ---
elif not uploaded_file and st.session_state.zip_operation_status == "success" and st.session_state.output_zip_content:
    status_placeholder.success("Showing previous successful result.")
    # Add Download Button
    download_placeholder.download_button(
        label=f"Download {st.session_state.output_zip_filename}",
        data=st.session_state.output_zip_content,
        file_name=st.session_state.output_zip_filename,
        mime='application/zip'
    )

st.markdown("---")
# Add a button to clear state if needed
if st.button("Clear ZIP Result"):
    st.session_state.output_zip_content = None
    st.session_state.output_zip_filename = None
    st.session_state.zip_operation_status = None
    # Force a rerun to clear widgets state indirectly
    st.rerun()
