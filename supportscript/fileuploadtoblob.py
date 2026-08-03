# Define "file_upload_to_blob" Function
def file_upload_to_blob(env_file_path: str, upload_file_path: str, upload_file_hash_value: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '1', 'message': str(error)}

    # Check If Both File Path Is Present And File:S2
    try:
        upload_file_path_object = Path(upload_file_path)
        if upload_file_path_object.exists() and upload_file_path_object.is_file():
            print('INFO - File Exists And Is A File')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '2', 'message': str(error)}

    # Load Environment File:S3
    try:
        if Path(env_file_path).exists() and Path(env_file_path).is_file():
            load_dotenv(dotenv_path = Path(env_file_path))
            print(f'INFO - Environment File Loaded: {env_file_path}')
        else:
            return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '3', 'message': 'Environment File Not Found'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '3', 'message': str(error)}

    # Creating Azure BLOB Service Client:S4
    try:
        blob_service_client = BlobServiceClient.from_connection_string(str(os.getenv('BLOB_CONNECTION_STRING')))
        blob_container_client = blob_service_client.get_container_client(str(os.getenv('BLOB_CONTAINER_NAME')))
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '4', 'message': str(error)}

    # Delete All Existing BLOBs From Container:S5
    try:
        for blob_file_path in blob_container_client.list_blobs():
            blob_container_client.delete_blob(blob_file_path.name)
        print('INFO - All Existing BLOBs Deleted From Container')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '5', 'message': str(error)}

    # Upload File To Azure BLOB:S6
    try:
        upload_file_blob_client = blob_container_client.get_blob_client(upload_file_path_object.name)
        with open(upload_file_path, 'rb') as local_file_data:
            upload_file_blob_client.upload_blob(
                local_file_data,
                overwrite = True,
                content_settings = ContentSettings(content_md5 = upload_file_hash_value) #type: ignore
            )
        print(f'INFO - File Uploaded To BLOB: {upload_file_path_object.name}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '6', 'message': str(error)}