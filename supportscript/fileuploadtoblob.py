# Define "file_upload_to_blob" Function
def file_upload_to_blob(env_file_path: str, upload_file_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        import hashlib
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

    # Calculate File MD5 Hash And File Size:S3
    try:
        with open(upload_file_path, 'rb') as local_file_data:
            md5_hash = hashlib.md5(local_file_data.read())
        upload_file_hash_value = md5_hash.hexdigest()
        upload_file_hash_bytes = md5_hash.digest()
        upload_file_size = upload_file_path_object.stat().st_size
        print(f'INFO - File MD5 Hash Calculated: {upload_file_hash_value}')
        print(f'INFO - File Size Calculated: {upload_file_size} bytes')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '3', 'message': str(error)}

    # Load Environment File:S4
    try:
        if Path(env_file_path).exists() and Path(env_file_path).is_file():
            load_dotenv(dotenv_path = Path(env_file_path))
            print(f'INFO - Environment File Loaded: {env_file_path}')
        else:
            return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '4', 'message': 'Environment File Not Found'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '4', 'message': str(error)}

    # Creating Azure BLOB Service Client:S5
    try:
        blob_service_client = BlobServiceClient.from_connection_string(str(os.getenv('BLOB_CONNECTION_STRING')))
        blob_container_client = blob_service_client.get_container_client(str(os.getenv('BLOB_CONTAINER_NAME')))
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '5', 'message': str(error)}

    # Delete All Existing BLOBs From Container:S6
    try:
        for blob_file_path in blob_container_client.list_blobs():
            blob_container_client.delete_blob(blob_file_path.name)
        print('INFO - All Existing BLOBs Deleted From Container')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '6', 'message': str(error)}

    # Upload File To Azure BLOB:S7
    try:
        upload_file_blob_client = blob_container_client.get_blob_client(upload_file_path_object.name)
        with open(upload_file_path, 'rb') as local_file_data:
            upload_file_blob_client.upload_blob(
                local_file_data,
                overwrite = True,
                content_settings = ContentSettings(content_md5 = upload_file_hash_bytes) #type: ignore
            )
        print(f'INFO - File Uploaded To BLOB: {upload_file_path_object.name}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '7', 'message': str(error)}

    # Verify Uploaded File Size And MD5:S8
    try:
        blob_properties = upload_file_blob_client.get_blob_properties()
        if (upload_file_size == blob_properties.size) and (upload_file_hash_bytes == blob_properties.content_settings.content_md5):
            print('INFO - Uploaded File Size And MD5 Verified Successfully')
        else:
            return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '8', 'message': 'Uploaded File Size Or MD5 Verification Failed'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '8', 'message': str(error)}

    # Create Directories In Azure BLOB Container:S9
    try:
        for directory_name in ['FileDownload', 'FileUpload']:
            directory_blob_client = blob_container_client.get_blob_client(f'{directory_name}/')
            directory_blob_client.upload_blob(b'', overwrite = True)
            print(f'INFO - Directory Created In Azure BLOB Container: {directory_name}/')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Upload-To-BLOB', 'step': '9', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'File-Upload-To-BLOB', 'step': '9', 'message': 'File Uploaded And Verified Successfully'}