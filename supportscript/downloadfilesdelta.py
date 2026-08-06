# Define "download_files_delta" Function
def download_files_delta(env_file_path: str, database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        import json
        from supportscript.filedownloadfromblob import file_download_from_blob
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '1', 'message': str(error)}

    # Check Env, Database And JSON File Present:S2
    try:
        env_file_object = Path(env_file_path)
        if not env_file_object.exists() or not env_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '2', 'message': f'Environment File Not Found Or Not A File: "{Path(env_file_path).name}"'}

        database_file_object = Path(database_file_path)
        if not database_file_object.exists() or not database_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '2', 'message': f'Database File Not Found Or Not A File: "{Path(database_file_path).name}"'}

        json_dump_file_object = Path(json_dump_file_path)
        if not json_dump_file_object.exists() or not json_dump_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '2', 'message': f'JSON Dump File Not Found Or Not A File: "{Path(json_dump_file_path).name}"'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '2', 'message': str(error)}

    # Delete And Recreate FilesDelta Folder:S3
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Folder Deleted And Recreated: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '3', 'message': str(error)}

    # Download File Hash Details From Azure BLOB:S4
    try:
        file_hash_download_result = file_download_from_blob(
            env_file_path = env_file_path,
            files_delta_store_folder_path = files_delta_store_folder_path,
            file_hash_download = True
        )
        if file_hash_download_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '4', 'message': f'Failed To Download File Hash Details: {file_hash_download_result.get("message")}'}
        print(f'{"[INFO]":<10} File Hash Details Downloaded From Azure BLOB')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '4', 'message': str(error)}

    # Load Downloaded File Hash Details JSON:S5
    try:
        file_hash_details_json_path = Path(files_delta_store_folder_path) / 'FileHashDetails.json'
        with open(file_hash_details_json_path, 'r', encoding = 'utf-8') as file_hash_details_json_data:
            blob_file_hash_details_json_object = json.load(file_hash_details_json_data)
        print(f'{"[INFO]":<10} File Hash Details JSON Loaded Successfully: "{file_hash_details_json_path.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '5', 'message': str(error)}

    # Load Local File Hash Details JSON:S6
    try:
        with open(json_dump_file_path, 'r', encoding = 'utf-8') as json_dump_file_data:
            local_file_hash_details_json_object = json.load(json_dump_file_data)
        print(f'{"[INFO]":<10} Local File Hash Details JSON Loaded Successfully: "{Path(json_dump_file_path).name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '6', 'message': str(error)}

    # Compare BLOB And Local File Hash Details And Categorize By File Status:S7
    try:
        add_files_details = {}
        modified_files_details = {}
        delete_files_details = {}

        # Identify Added And Modified Files From BLOB
        for file_path, blob_file_details in blob_file_hash_details_json_object.items():
            local_file_details = local_file_hash_details_json_object.get(file_path)
            if local_file_details is None:
                # File exists in BLOB but not in local -> Add
                add_files_details[file_path] = dict(blob_file_details)
                add_files_details[file_path]['file_status'] = 'Add'
            else:
                # File exists in both -> check if hash changed
                if blob_file_details.get('file_hash_value') != local_file_details.get('file_hash_value'):
                    modified_files_details[file_path] = dict(blob_file_details)
                    modified_files_details[file_path]['file_status'] = 'Modified'

        # Identify Deleted Files From Local (not in BLOB)
        for file_path, local_file_details in local_file_hash_details_json_object.items():
            if file_path not in blob_file_hash_details_json_object:
                delete_files_details[file_path] = dict(local_file_details)
                delete_files_details[file_path]['file_status'] = 'Delete'

        print(f'{"[INFO]":<10} Total Added Files Details Created: {len(add_files_details)}')
        print(f'{"[INFO]":<10} Total Modified Files Details Created: {len(modified_files_details)}')
        print(f'{"[INFO]":<10} Total Deleted Files Details Created: {len(delete_files_details)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '7', 'message': str(error)}