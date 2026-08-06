# Define "blob_files_operation" Function
def blob_files_operation(
    operation: str,
    env_file_path: str,
    files_delta_store_folder_path: str | None = None,
    file_hash_download: bool = False,
    upload_file_path: str | None = None,
    hash_file_delete: bool = False
) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        import hashlib
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '1', 'message': str(error)}

    # Normalize And Validate Operation:S2
    try:
        operation = str(operation).strip().lower()
        if operation not in ('download', 'upload', 'clear'):
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '2', 'message': f'Invalid Operation: "{operation}". Supported Operations: download, upload, clear'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '2', 'message': str(error)}

    # Initialize Operation-Specific Variables
    files_delta_store_folder_path_object: Path | None = None
    upload_file_path_object: Path | None = None
    upload_file_hash_value: str = ''
    upload_file_hash_bytes: bytes = b''
    upload_file_size: int = 0

    # Operation-Specific Pre-Validation And Setup:S3
    try:
        if operation == 'download':
            if files_delta_store_folder_path is None:
                return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '3', 'message': 'Parameter "files_delta_store_folder_path" Is Required For Download Operation'}
            files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
            if files_delta_store_folder_path_object.exists() and files_delta_store_folder_path_object.is_dir():
                print(f'{"[INFO]":<10} Folder Exists: "{files_delta_store_folder_path_object.name}"')
            else:
                files_delta_store_folder_path_object.mkdir(parents=True, exist_ok=True)
                print(f'{"[INFO]":<10} Folder Created: "{files_delta_store_folder_path_object.name}"')
        elif operation == 'upload':
            if upload_file_path is None:
                return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '3', 'message': 'Parameter "upload_file_path" Is Required For Upload Operation'}
            upload_file_path_object = Path(upload_file_path)
            if not (upload_file_path_object.exists() and upload_file_path_object.is_file()):
                return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '3', 'message': 'Upload File Not Found Or Not A File'}
            md5_hash = hashlib.md5()
            with open(upload_file_path, 'rb') as local_file_data:
                while chunk := local_file_data.read(4 * 1024 * 1024):
                    md5_hash.update(chunk)
            upload_file_hash_value = md5_hash.hexdigest()
            upload_file_hash_bytes = md5_hash.digest()
            upload_file_size = upload_file_path_object.stat().st_size
            print(f'{"[INFO]":<10} File MD5 Hash Calculated: "{upload_file_hash_value}"')
            print(f'{"[INFO]":<10} File Size Calculated: {upload_file_size} bytes')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '3', 'message': str(error)}

    # Load Environment File:S4
    try:
        if Path(env_file_path).exists() and Path(env_file_path).is_file():
            load_dotenv(dotenv_path=Path(env_file_path))
            print(f'{"[INFO]":<10} Environment File Loaded')
        else:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '4', 'message': 'Environment File Not Found'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '4', 'message': str(error)}

    # Creating Azure BLOB Service Client:S5
    try:
        blob_service_client = BlobServiceClient.from_connection_string(str(os.getenv('BLOB_CONNECTION_STRING')))
        blob_container_client = blob_service_client.get_container_client(str(os.getenv('BLOB_CONTAINER_NAME')))
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '5', 'message': str(error)}

    # Execute Requested BLOB Operation
    if operation == 'download':
        assert files_delta_store_folder_path_object is not None
        # Fetch Blob List From Azure BLOB Container:S6
        try:
            blob_name_list = [blob_properties.name for blob_properties in blob_container_client.list_blobs()]
            print(f'{"[INFO]":<10} Blob List Fetched From Container. Total BLOBs Found: {len(blob_name_list)}')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '6', 'message': str(error)}

        # Prepare Local File Path List For Download:S7
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
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': str(error)}

        # Download File(s) From Azure BLOB:S8
        try:
            blob_file_dict = {}
            for local_file_path in local_file_path_list:
                if file_hash_download:
                    blob_name = 'FileHashDetails.json'
                else:
                    blob_name = f'FilesDeltaStore/{local_file_path.relative_to(files_delta_store_folder_path_object).as_posix()}'
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_file_path, 'wb') as local_file_data:
                    local_file_data.write(blob_container_client.get_blob_client(blob_name).download_blob().readall())
                blob_properties = blob_container_client.get_blob_client(blob_name).get_blob_properties()
                blob_file_dict[str(local_file_path)] = blob_properties.content_settings.content_md5
                local_file_relative_path = local_file_path.relative_to(files_delta_store_folder_path_object).as_posix()
                local_file_display_path = f'{files_delta_store_folder_path_object.name}/{local_file_relative_path}'
                print(f'{"[INFO]":<10} File Downloaded From BLOB: "{Path(blob_name).name}" -> "{Path(local_file_display_path).name}"')
            print(f'{"[INFO]":<10} Total Files Downloaded: {len(blob_file_dict)}')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '8', 'message': str(error)}

        # Calculate Local File MD5 Hashes:S9
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
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '9', 'message': str(error)}

        # Compare BLOB And Local File MD5 Hashes:S10
        try:
            if set(blob_file_dict.keys()) != set(downloaded_file_dict.keys()):
                return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '10', 'message': 'Downloaded File List Does Not Match BLOB File List'}
            for file_path, local_md5_hash in downloaded_file_dict.items():
                blob_md5_hash = blob_file_dict[file_path]
                if blob_md5_hash.hex() != local_md5_hash:
                    return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '10', 'message': f'MD5 Mismatch Detected For File: "{Path(file_path).name}"'}
            return {'status': 'SUCCESS', 'script_name': 'BLOB-Files-Operation', 'step': '10', 'message': 'All Downloaded Files MD5 Hashes Verified Successfully'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '10', 'message': str(error)}

    elif operation == 'upload':
        assert upload_file_path is not None
        assert upload_file_path_object is not None
        # Upload File To Azure BLOB:S6
        try:
            if upload_file_path_object.name == 'FileHashDetails.json':
                upload_file_blob_client = blob_container_client.get_blob_client(upload_file_path_object.name)
            else:
                posix_path = upload_file_path_object.as_posix()
                marker = 'FilesDeltaStore/'
                idx = posix_path.find(marker)
                if idx != -1:
                    blob_name = posix_path[idx:]
                else:
                    blob_name = f'FilesDeltaStore/{upload_file_path_object.name}'
                upload_file_blob_client = blob_container_client.get_blob_client(blob_name)
            with open(upload_file_path, 'rb') as local_file_data:
                upload_file_blob_client.upload_blob(
                    local_file_data,
                    overwrite=True,
                    content_settings=ContentSettings(content_md5=upload_file_hash_bytes) #type: ignore
                )
            print(f'{"[INFO]":<10} File Uploaded To BLOB: "{Path(upload_file_blob_client.blob_name).name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '6', 'message': str(error)}

        # Verify Uploaded File Size And MD5:S7
        try:
            blob_properties = upload_file_blob_client.get_blob_properties()
            if (upload_file_size == blob_properties.size) and (upload_file_hash_bytes == blob_properties.content_settings.content_md5):
                print(f'{"[INFO]":<10} Uploaded File Size And MD5 Verified Successfully')
                return {'status': 'SUCCESS', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': 'File Uploaded And Verified Successfully'}
            else:
                return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': 'Uploaded File Size Or MD5 Verification Failed'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': str(error)}

    elif operation == 'clear':
        # Delete All Existing BLOBs From Container:S6
        try:
            for blob_file_path in blob_container_client.list_blobs():
                if hash_file_delete or blob_file_path.name != 'FileHashDetails.json':
                    blob_container_client.delete_blob(blob_file_path.name)
            if hash_file_delete:
                print(f'{"[INFO]":<10} All Existing BLOBs Deleted From Container Including "FileHashDetails.json"')
            else:
                print(f'{"[INFO]":<10} All Existing BLOBs Deleted From Container Except "FileHashDetails.json"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '6', 'message': str(error)}

        # Verify All BLOBs Deleted Based On hash_file_delete Parameter:S7
        try:
            remaining_blobs = [blob.name for blob in blob_container_client.list_blobs()]
            if hash_file_delete:
                if len(remaining_blobs) == 0:
                    print(f'{"[INFO]":<10} Verified: Container Is Empty')
                    return {'status': 'SUCCESS', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': 'Container Cleared Successfully Including "FileHashDetails.json"'}
                else:
                    return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': f'Unexpected BLOBs Still Present: {", ".join(Path(blob).name for blob in remaining_blobs)}'}
            else:
                if (len(remaining_blobs) == 0) or (len(remaining_blobs) == 1 and remaining_blobs[0] == 'FileHashDetails.json'):
                    print(f'{"[INFO]":<10} Verified: Only "FileHashDetails.json" Remains In Container')
                    return {'status': 'SUCCESS', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': 'Container Cleared Successfully Except "FileHashDetails.json"'}
                else:
                    return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': f'Unexpected BLOBs Still Present: {", ".join(Path(blob).name for blob in remaining_blobs)}'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'BLOB-Files-Operation', 'step': '7', 'message': str(error)}
