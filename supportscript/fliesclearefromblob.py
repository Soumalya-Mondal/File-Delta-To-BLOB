# Define "files_clear_from_blob" Function
def files_clear_from_blob(env_file_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '10', 'message': str(error)}