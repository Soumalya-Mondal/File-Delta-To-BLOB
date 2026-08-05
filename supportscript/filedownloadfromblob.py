# Define "file_download_from_blob" Function
def file_download_from_blob(env_file_path: str, files_delta_store_folder_path: str, file_hash_download: bool = False) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        import hashlib
        from azure.storage.blob import BlobServiceClient
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '1', 'message': str(error)}

    # Check If "files_delta_store_folder_path" Folder Exists Or Create It:S2
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists() and files_delta_store_folder_path_object.is_dir():
            print(f'{"[INFO]":<10} Folder Exists: "{files_delta_store_folder_path_object.name}"')
        else:
            files_delta_store_folder_path_object.mkdir(parents=True, exist_ok=True)
            print(f'{"[INFO]":<10} Folder Created: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '2', 'message': str(error)}

    # Load Environment File:S3
    try:
        if Path(env_file_path).exists() and Path(env_file_path).is_file():
            load_dotenv(dotenv_path=Path(env_file_path))
            print(f'{"[INFO]":<10} Environment File Loaded')
        else:
            return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '3', 'message': 'Environment File Not Found'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '3', 'message': str(error)}

    # Creating Azure BLOB Service Client:S4
    try:
        blob_service_client = BlobServiceClient.from_connection_string(str(os.getenv('BLOB_CONNECTION_STRING')))
        blob_container_client = blob_service_client.get_container_client(str(os.getenv('BLOB_CONTAINER_NAME')))
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '4', 'message': str(error)}

    # Fetch Blob List From Azure BLOB Container:S5
    try:
        blob_name_list = [blob_properties.name for blob_properties in blob_container_client.list_blobs()]
        print(f'{"[INFO]":<10} Blob List Fetched From Container. Total BLOBs Found: {len(blob_name_list)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '5', 'message': str(error)}

    # Prepare Local File Path List For Download:S6
    try:
        local_file_path_list = []
        for blob_name in blob_name_list:
            if file_hash_download:
                if blob_name != 'FileHashDetails.json':
                    continue
                local_file_path = files_delta_store_folder_path_object / 'FileHashDetails.json'
            else:
                if blob_name == 'FileHashDetails.json':
                    continue
                if blob_name.startswith('FilesDeltaStore/'):
                    local_file_path = files_delta_store_folder_path_object / blob_name[len('FilesDeltaStore/'):]
                else:
                    continue
            local_file_path_list.append(local_file_path)
        print(f'{"[INFO]":<10} Local File Path List Prepared. Total Files To Download: {len(local_file_path_list)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '6', 'message': str(error)}

    # Download File(s) From Azure BLOB:S7
    try:
        blob_file_dict = {}
        for local_file_path in local_file_path_list:
            if file_hash_download:
                blob_name = 'FileHashDetails.json'
            else:
                blob_name = f'FilesDeltaStore/{local_file_path.relative_to(files_delta_store_folder_path_object).as_posix()}'

            local_file_path.parent.mkdir(parents = True, exist_ok = True)
            with open(local_file_path, 'wb') as local_file_data:
                local_file_data.write(blob_container_client.get_blob_client(blob_name).download_blob().readall())
            blob_properties = blob_container_client.get_blob_client(blob_name).get_blob_properties()
            blob_file_dict[str(local_file_path)] = blob_properties.content_settings.content_md5
            local_file_relative_path = local_file_path.relative_to(files_delta_store_folder_path_object).as_posix()
            local_file_display_path = f'{files_delta_store_folder_path_object.name}/{local_file_relative_path}'
            print(f'{"[INFO]":<10} File Downloaded From BLOB: "{Path(blob_name).name}" -> "{Path(local_file_display_path).name}"')
        print(f'{"[INFO]":<10} Total Files Downloaded: {len(blob_file_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '7', 'message': str(error)}

    # Calculate Local File MD5 Hashes:S8
    try:
        downloaded_file_dict = {}
        for local_file_path in files_delta_store_folder_path_object.rglob('*'):
            if not local_file_path.is_file():
                continue
            if file_hash_download:
                if local_file_path.name != 'FileHashDetails.json':
                    continue
            else:
                if local_file_path.name == 'FileHashDetails.json':
                    continue
            md5_hash = hashlib.md5()
            with open(local_file_path, 'rb') as local_file_data:
                while chunk := local_file_data.read(4 * 1024 * 1024):
                    md5_hash.update(chunk)
            downloaded_file_dict[str(local_file_path)] = md5_hash.hexdigest()
        print(f'{"[INFO]":<10} Total Local File MD5 Hashes Calculated: {len(downloaded_file_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '8', 'message': str(error)}

    # Compare BLOB And Local File MD5 Hashes:S9
    try:
        if set(blob_file_dict.keys()) != set(downloaded_file_dict.keys()):
            return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '9', 'message': 'Downloaded File List Does Not Match BLOB File List'}

        for file_path, local_md5_hash in downloaded_file_dict.items():
            blob_md5_hash = blob_file_dict[file_path]
            if blob_md5_hash.hex() != local_md5_hash:
                return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '9', 'message': f'MD5 Mismatch Detected For File: "{Path(file_path).name}"'}

        return {'status': 'SUCCESS', 'script_name': 'File-Download-From-BLOB', 'step': '9', 'message': 'All Downloaded Files MD5 Hashes Verified Successfully'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Download-From-BLOB', 'step': '9', 'message': str(error)}