# Define "files_clear_from_blob" Function
def files_clear_from_blob(env_file_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        from azure.storage.blob import BlobServiceClient
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '1', 'message': str(error)}

    # Load Environment File:S2
    try:
        if Path(env_file_path).exists() and Path(env_file_path).is_file():
            load_dotenv(dotenv_path = Path(env_file_path))
            print(f'{"[INFO]":<10} Environment File Loaded')
        else:
            return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '2', 'message': 'Environment File Not Found'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '2', 'message': str(error)}

    # Creating Azure BLOB Service Client:S3
    try:
        blob_service_client = BlobServiceClient.from_connection_string(str(os.getenv('BLOB_CONNECTION_STRING')))
        blob_container_client = blob_service_client.get_container_client(str(os.getenv('BLOB_CONTAINER_NAME')))
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '3', 'message': str(error)}

    # Delete All Existing BLOBs From Container:S4
    try:
        for blob_file_path in blob_container_client.list_blobs():
            if blob_file_path.name != 'FileHashDetails.json':
                blob_container_client.delete_blob(blob_file_path.name)
        print(f'{"[INFO]":<10} All Existing BLOBs Deleted From Container Except "FileHashDetails.json"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '4', 'message': str(error)}

    # Verify All BLOBs Deleted Except "FileHashDetails.json":S5
    try:
        remaining_blobs = [blob.name for blob in blob_container_client.list_blobs()]
        if (len(remaining_blobs) == 0) or (len(remaining_blobs) == 1 and remaining_blobs[0] == 'FileHashDetails.json'):
            print(f'{"[INFO]":<10} Verified: Only "FileHashDetails.json" Remains In Container')
            return {'status': 'SUCCESS', 'script_name': 'Files-Clear-From-BLOB', 'step': '5', 'message': 'Container Cleared Successfully Except "FileHashDetails.json"'}
        else:
            return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '5', 'message': f'Unexpected BLOBs Still Present: {remaining_blobs}'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Files-Clear-From-BLOB', 'step': '5', 'message': str(error)}