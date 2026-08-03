# Define "rebase_files_details" function
def rebase_files_details(database_file_path: str, json_dump_file_path: str, rebase_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
    except Exception as error:
        return {'status' : 'ERROR', 'script_name' : 'Rebase-Files-Details', 'step' : '1', 'message' : str(error)}