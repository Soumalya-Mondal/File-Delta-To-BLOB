# Define "file_upload_to_blob" Function
def file_upload_to_blob(env_file_path: str, file_path: str, file_hash_value: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '1', 'message': str(error)}

    # Check If Both File Path Is Present And File:S2
    try:
        file_path_object = Path(file_path)
        if file_path_object.exists() and file_path_object.is_file():
            print('INFO - File Exists And Is A File')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '2', 'message': str(error)}