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
    printable_command = []
    password_found = False
    for i, arg in enumerate(command):
        if arg == '-P' and i + 1 < len(command):
            printable_command.extend([arg, '********'])
            password_found = True
        elif password_found:
            password_found = False
            continue
        else:
            printable_command.append(arg)

    try:
        process = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=120
        )
        success = process.returncode == 0
        if not success:
            err_lower = process.stderr.lower()
            if "nothing to do" in err_lower:
                 st.error(f"Zip Error (Exit Code {process.returncode}): Nothing to zip. Check input file path.\n```\n{process.stderr.strip()}\n```")
            else:
                 st.error(f"Zip Error (Exit Code {process.returncode}):\n```\n{process.stderr.strip()}\n```")
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

check_zip_command()

# --- Session State Initialization ---
# For storing results
if 'output_zip_content' not in st.session_state:
    st.session_state.output_zip_content = None
if 'output_zip_filename' not in st.session_state:
    st.session_state.output_zip_filename = None
if 'zip_operation_status' not in st.session_state:
    st.session_state.zip_operation_status = None

# For forcing widget reset
if 'zip_clear_trigger' not in st.session_state:
    st.session_state.zip_clear_trigger = 0 # Initialize clear trigger

# --- UI Elements ---
st.info("**Note:** This tool currently supports zipping a single file.", icon="ℹ️")

# Use the clear trigger in the key to force reset when trigger changes
uploader_key = f"zip_uploader_{st.session_state.zip_clear_trigger}"
uploaded_file = st.file_uploader(
    "Choose the file to zip",
    type=None,
    key=uploader_key
)

st.markdown("### Set ZIP Password")
col1, col2 = st.columns(2)
# Use the clear trigger in the keys
pwd1_key = f"zip_pwd1_{st.session_state.zip_clear_trigger}"
pwd2_key = f"zip_pwd2_{st.session_state.zip_clear_trigger}"
with col1:
    password = st.text_input("Enter Password:", type="password", key=pwd1_key)
with col2:
    password_confirm = st.text_input("Confirm Password:", type="password", key=pwd2_key)

# Output Filename Suggestion/Input
default_output_filename = ""
if uploaded_file:
    input_base, _ = os.path.splitext(uploaded_file.name)
    default_output_filename = f"{input_base}_protected.zip"

# Use the clear trigger in the key
output_name_key = f"zip_output_name_{st.session_state.zip_clear_trigger}"
output_filename_user = st.text_input(
    "Desired Output ZIP Filename:",
    value=default_output_filename, # Default value will reappear after clear
    placeholder="e.g., protected_archive.zip",
    key=output_name_key
)

# Action Button and Status Area
st.markdown("---")
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
    # Reset previous results before processing
    st.session_state.output_zip_content = None
    st.session_state.output_zip_filename = None
    st.session_state.zip_operation_status = None
    status_placeholder.info("Processing...")
    download_placeholder.empty()

    # Input Validation... (rest of the validation code remains the same)
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
        # Modify the value directly in the widget state before using it
        # This is less clean, perhaps just use the modified name later
        actual_output_filename = output_filename_user + ".zip"
        st.warning(f"Output filename didn't end with '.zip'. Using '{actual_output_filename}'.")
    else:
        actual_output_filename = output_filename_user


    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        input_file_path = os.path.join(temp_dir, uploaded_file.name)
        # Use the potentially modified filename
        output_file_path = os.path.join(temp_dir, actual_output_filename)

        with open(input_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        args = [
            '-j', '-e', '-P', password,
            output_file_path, input_file_path
        ]

        success, stdout, stderr = run_zip_command(args, password)

        if success and os.path.exists(output_file_path):
            st.session_state.zip_operation_status = "success"
            with open(output_file_path, "rb") as f:
                st.session_state.output_zip_content = f.read()
            # Store the actual filename used
            st.session_state.output_zip_filename = actual_output_filename

            status_placeholder.success("Password-protected ZIP created successfully!")
            download_placeholder.download_button(
                label=f"Download {st.session_state.output_zip_filename}",
                data=st.session_state.output_zip_content,
                file_name=st.session_state.output_zip_filename,
                mime='application/zip'
            )
        else:
            st.session_state.zip_operation_status = "fail"
            status_placeholder.error("Failed to create ZIP file. See details above.")
            if os.path.exists(output_file_path):
                try: os.remove(output_file_path)
                except OSError: pass

    except Exception as e:
        status_placeholder.error(f"An error occurred during ZIP processing: {e}")
        st.session_state.zip_operation_status = "fail"
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except Exception as e: st.warning(f"Could not clean up temp dir {temp_dir}: {e}")

# --- Display previous successful results ---
# (This logic remains the same)
elif not uploaded_file and st.session_state.zip_operation_status == "success" and st.session_state.output_zip_content:
    status_placeholder.success("Showing previous successful result.")
    download_placeholder.download_button(
        label=f"Download {st.session_state.output_zip_filename}",
        data=st.session_state.output_zip_content,
        file_name=st.session_state.output_zip_filename,
        mime='application/zip'
    )

st.markdown("---")

# --- Clear All Button ---
# Changed label to "Clear All"
if st.button("Clear All"):
    # Reset results
    st.session_state.output_zip_content = None
    st.session_state.output_zip_filename = None
    st.session_state.zip_operation_status = None
    # Increment the trigger to change widget keys
    st.session_state.zip_clear_trigger += 1
    # Rerun the script to apply changes
    st.rerun()
