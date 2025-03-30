import streamlit as st
import subprocess
import os
import tempfile
import shutil
import mimetypes # To guess file types for preview

# --- Configuration ---
OPENSSL_COMMAND = "openssl"
ENCRYPTION_CIPHER = "aes-256-cbc"
PREVIEW_SIZE_LIMIT = 5 * 1024 * 1024 # Limit preview size to 5MB to avoid browser slowdown
PREVIEW_LINES_LIMIT = 100 # Max lines for text preview

# --- Helper Functions ---

def check_openssl():
    """Checks if the openssl command is available in the system PATH."""
    if shutil.which(OPENSSL_COMMAND) is None:
        st.error(f"CRITICAL ERROR: '{OPENSSL_COMMAND}' command not found. Please ensure OpenSSL is installed and in the system PATH.")
        st.stop()

def run_openssl_command(args, password):
    """
    Runs the openssl command with given arguments and password.
    Returns tuple: (success_boolean, stdout_str, stderr_str)
    """
    command = [OPENSSL_COMMAND] + args
    # Use -pass pass:PASSWORD for non-interactive password input
    # SECURITY WARNING: Passing password on command line can be a risk in multi-user systems.
    command.extend(['-pass', f'pass:{password}'])

    printable_command = [arg if not arg.startswith('pass:') else 'pass:********' for arg in command]
    #st.write(f"DEBUG: Running command: `{' '.join(printable_command)}`") # For debugging

    try:
        # Use a timeout to prevent hangs (e.g., if openssl waits unexpectedly)
        process = subprocess.run(
            command,
            check=False, # Don't raise exception on non-zero exit, we check manually
            capture_output=True,
            text=True,
            timeout=60 # Timeout in seconds
        )
        success = process.returncode == 0
        if not success:
            st.error(f"OpenSSL Error (Exit Code {process.returncode}):\n```\n{process.stderr.strip()}\n```")
        # Also print stderr if openssl succeeded but printed warnings
        elif process.stderr:
             st.warning(f"OpenSSL Messages (stderr):\n```\n{process.stderr.strip()}\n```")

        return success, process.stdout.strip(), process.stderr.strip()

    except subprocess.TimeoutExpired:
        st.error("OpenSSL command timed out after 60 seconds.")
        return False, "", "Timeout expired"
    except FileNotFoundError:
         st.error(f"Error: The '{OPENSSL_COMMAND}' command was not found. Is OpenSSL installed and in PATH?")
         return False, "", f"Command not found: {OPENSSL_COMMAND}"
    except Exception as e:
        st.error(f"An unexpected error occurred while running OpenSSL: {e}")
        return False, "", str(e)


def get_file_preview(file_path):
    """Generates a preview string for a file, handling text and binary."""
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return "(File is empty)"
        if file_size > PREVIEW_SIZE_LIMIT:
            return f"(File is too large for preview: {file_size / (1024*1024):.2f} MB)"

        # Guess mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        is_likely_text = mime_type and mime_type.startswith('text')

        with open(file_path, 'rb') as f:
            content_bytes = f.read(PREVIEW_SIZE_LIMIT) # Read up to limit

        if is_likely_text:
            try:
                content_str = content_bytes.decode('utf-8')
                lines = content_str.splitlines()
                if len(lines) > PREVIEW_LINES_LIMIT:
                     preview_content = "\n".join(lines[:PREVIEW_LINES_LIMIT]) + "\n... (truncated)"
                else:
                     preview_content = content_str
                return f"**Preview (first {PREVIEW_LINES_LIMIT} lines or {PREVIEW_SIZE_LIMIT/1024:.0f}KB):**\n```\n{preview_content}\n```"
            except UnicodeDecodeError:
                is_likely_text = False # Decoding failed, treat as binary

        # If not text or decoding failed
        hex_preview = content_bytes[:256].hex(' ') # Show first 256 bytes as hex
        return f"(Binary file detected or Text decoding failed)\n**Hex Preview (first 256 bytes):**\n```\n{hex_preview}\n...```"

    except Exception as e:
        return f"(Error generating preview: {e})"

# --- Streamlit App ---

st.set_page_config(
    page_title="Encrypt/Decrypt",
    page_icon="🔑"
)

st.title("🔑 Encrypt / Decrypt File")
st.markdown(f"Uses `openssl {ENCRYPTION_CIPHER} -pbkdf2`. Remember your password!")

# --- Check OpenSSL availability ---
check_openssl()

# --- Session State Initialization ---
if 'output_content' not in st.session_state:
    st.session_state.output_content = None
if 'output_filename' not in st.session_state:
    st.session_state.output_filename = None
if 'operation_status' not in st.session_state:
    st.session_state.operation_status = None # Can be "success", "fail", or None

# --- UI Elements ---
operation = st.radio("Select Operation:", ("Encrypt", "Decrypt"), horizontal=True)

uploaded_file = st.file_uploader("Choose a file or drag and drop", type=None) # Allow any type

# Input Preview Area
input_preview_placeholder = st.empty()

# Password Input
col1, col2 = st.columns(2)
with col1:
    password = st.text_input("Enter Password:", type="password", key="pwd1")
with col2:
    if operation == "Encrypt":
        password_confirm = st.text_input("Confirm Password:", type="password", key="pwd2")
    else:
        # Add a placeholder to keep layout consistent during decryption
        st.container() # Empty container

# Output Filename Suggestion/Input
default_output_filename = ""
if uploaded_file:
    input_base, input_ext = os.path.splitext(uploaded_file.name)
    if operation == "Encrypt":
        default_output_filename = f"{input_base}.enc"
    else: # Decrypt
        # Try to intelligently remove .enc, otherwise add .dec
        if input_ext.lower() == '.enc':
            default_output_filename = input_base if input_base else "decrypted_file"
        else:
            default_output_filename = f"{uploaded_file.name}.dec" # Decrypt non-.enc file? Risky but possible.

output_filename_user = st.text_input(
    "Desired Output Filename:",
    value=default_output_filename,
    placeholder=default_output_filename if default_output_filename else "e.g., output.txt or archive.zip.enc"
)

# Action Button and Status Area
st.markdown("---")
run_button = st.button(f"Run {operation}", type="primary", disabled=not uploaded_file)
status_placeholder = st.empty()
output_preview_placeholder = st.empty()
download_placeholder = st.empty()

# --- Logic Execution ---
if run_button and uploaded_file:
    # Reset previous results
    st.session_state.output_content = None
    st.session_state.output_filename = None
    st.session_state.operation_status = None
    status_placeholder.info(f"Processing {operation}...")
    output_preview_placeholder.empty()
    download_placeholder.empty()

    # --- Input Validation ---
    if not password:
        status_placeholder.error("Password cannot be empty.")
        st.stop()
    if operation == "Encrypt" and password != password_confirm:
        status_placeholder.error("Passwords do not match.")
        st.stop()
    if not output_filename_user:
        status_placeholder.error("Output filename cannot be empty.")
        st.stop()

    # --- File Handling & OpenSSL Execution ---
    temp_dir = None # Initialize to ensure it's defined for finally block
    try:
        # Create a temporary directory to hold input and output files safely
        temp_dir = tempfile.mkdtemp()
        input_file_path = os.path.join(temp_dir, uploaded_file.name)
        output_file_path = os.path.join(temp_dir, output_filename_user) # Use user-defined name directly

        # Write uploaded content to the temporary input file
        with open(input_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Display input preview (now that the temp file exists)
        with input_preview_placeholder.expander("Preview Input File", expanded=False):
             st.write(f"**Filename:** `{uploaded_file.name}`")
             st.write(f"**Size:** `{uploaded_file.size / 1024:.2f} KB`")
             st.markdown(get_file_preview(input_file_path))


        # Prepare OpenSSL arguments
        args = ['enc', f'-{ENCRYPTION_CIPHER}', '-pbkdf2']
        if operation == "Decrypt":
            args.append('-d')
        elif operation == "Encrypt":
             args.append('-p') # Print salt/key/iv for encryption as per original spec

        args.extend(['-in', input_file_path, '-out', output_file_path])

        # Run the command
        success, stdout, stderr = run_openssl_command(args, password)

        if success and os.path.exists(output_file_path):
            st.session_state.operation_status = "success"
            # Read the output file content for download and preview
            with open(output_file_path, "rb") as f:
                st.session_state.output_content = f.read()
            st.session_state.output_filename = output_filename_user # Store the intended filename

            status_placeholder.success(f"{operation} successful!")

            # Display Output Preview
            with output_preview_placeholder.expander("Preview Output File", expanded=True):
                 st.write(f"**Filename:** `{st.session_state.output_filename}`")
                 output_size = len(st.session_state.output_content)
                 st.write(f"**Size:** `{output_size / 1024:.2f} KB`")
                 st.markdown(get_file_preview(output_file_path)) # Preview from temp file

            # Add Download Button
            download_placeholder.download_button(
                label=f"Download {st.session_state.output_filename}",
                data=st.session_state.output_content,
                file_name=st.session_state.output_filename,
                mime=mimetypes.guess_type(st.session_state.output_filename)[0] or 'application/octet-stream'
            )

        else:
            st.session_state.operation_status = "fail"
            # Error message already displayed by run_openssl_command
            status_placeholder.error(f"{operation} failed. See details above.")
            # Clean up potentially incomplete output file
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                except OSError:
                    pass # Ignore cleanup error


    except Exception as e:
        status_placeholder.error(f"An error occurred during processing: {e}")
        st.session_state.operation_status = "fail"
    finally:
        # --- Cleanup ---
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                # st.write(f"DEBUG: Cleaned up temp directory: {temp_dir}") # For debugging
            except Exception as e:
                st.warning(f"Could not automatically clean up temporary directory {temp_dir}: {e}")

# --- Display Input Preview if file uploaded but not processed yet ---
# (Also persists after processing if successful)
elif uploaded_file and st.session_state.operation_status != "fail": # Avoid showing preview if last op failed
     temp_dir_preview = None
     try:
        temp_dir_preview = tempfile.mkdtemp()
        preview_input_path = os.path.join(temp_dir_preview, uploaded_file.name)
        with open(preview_input_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        with input_preview_placeholder.expander("Preview Input File", expanded=False):
             st.write(f"**Filename:** `{uploaded_file.name}`")
             st.write(f"**Size:** `{uploaded_file.size / 1024:.2f} KB`")
             st.markdown(get_file_preview(preview_input_path))
     except Exception as e:
        input_preview_placeholder.warning(f"Could not generate input preview: {e}")
     finally:
        if temp_dir_preview:
            shutil.rmtree(temp_dir_preview)

# --- Display previous successful results if no new file is uploaded ---
elif not uploaded_file and st.session_state.operation_status == "success" and st.session_state.output_content:
    status_placeholder.success("Showing previous successful result.")
    # Display Output Preview
    with output_preview_placeholder.expander("Preview Previous Output File", expanded=True):
         st.write(f"**Filename:** `{st.session_state.output_filename}`")
         output_size = len(st.session_state.output_content)
         st.write(f"**Size:** `{output_size / 1024:.2f} KB`")
         # Can't easily re-preview from bytes, just show info
         st.info("Preview requires reprocessing. Download the file to view full content.")

    # Add Download Button
    download_placeholder.download_button(
        label=f"Download {st.session_state.output_filename}",
        data=st.session_state.output_content,
        file_name=st.session_state.output_filename,
        mime=mimetypes.guess_type(st.session_state.output_filename)[0] or 'application/octet-stream'
    )

st.markdown("---")
# Add a button to clear state if needed
if st.button("Clear All"):
    st.session_state.output_content = None
    st.session_state.output_filename = None
    st.session_state.operation_status = None
    # Force a rerun to clear widgets state indirectly (may need explicit clearing for some widgets if needed)
    st.rerun()
