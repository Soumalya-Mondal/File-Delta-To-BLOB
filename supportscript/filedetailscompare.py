# Define "file_details_compare" Function
def file_details_compare(env_file_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '1', 'message': str(error)}
