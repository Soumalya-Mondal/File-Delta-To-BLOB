# Define "upload_files_delta" Function
def upload_files_delta(env_file_path: str, database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        import json
        from supportscript.localfiledetailsupdate import local_file_details_update
        from supportscript.persistfiledetailsupdate import persist_file_details_update
        from supportscript.fileuploadtoblob import file_upload_to_blob
        from supportscript.filedownloadfromblob import file_download_from_blob
        from supportscript.fliesclearefromblob import files_clear_from_blob
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '1', 'message': str(error)}

    # Check Env, Database And JSON File Present:S2
    try:
        env_file_object = Path(env_file_path)
        if not env_file_object.exists() or not env_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '2', 'message': f'Environment File Not Found Or Not A File: "{Path(env_file_path).name}"'}

        database_file_object = Path(database_file_path)
        if not database_file_object.exists() or not database_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '2', 'message': f'Database File Not Found Or Not A File: "{Path(database_file_path).name}"'}

        json_dump_file_object = Path(json_dump_file_path)
        if not json_dump_file_object.exists() or not json_dump_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '2', 'message': f'JSON Dump File Not Found Or Not A File: "{Path(json_dump_file_path).name}"'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '2', 'message': str(error)}

    # Delete And Recreate FilesDelta Folder:S3
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Folder Deleted And Recreated: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '3', 'message': str(error)}

    # Download File Hash Details From Azure BLOB Container:S4
    try:
        download_result = file_download_from_blob(
            env_file_path = env_file_path,
            files_delta_store_folder_path = files_delta_store_folder_path,
            file_hash_download = True
        )
        if download_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '4', 'message': f'Failed To Download File Hash Details From Azure BLOB: {download_result.get("message")}'}
        print(f'{"[INFO]":<10} File Hash Details Downloaded From Azure BLOB')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '4', 'message': str(error)}

    # Load File Hash Details JSON File From BLOB:S5
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if not files_delta_store_folder_path_object.exists() or not files_delta_store_folder_path_object.is_dir():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '5', 'message': f'FilesDelta Folder Not Found Or Not A Directory: "{Path(files_delta_store_folder_path).name}"'}
        if not (files_delta_store_folder_path_object / 'FileHashDetails.json').exists() or not (files_delta_store_folder_path_object / 'FileHashDetails.json').is_file():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '5', 'message': f'FileHashDetails.json From BLOB Not Found Or Not A File: "{(files_delta_store_folder_path_object / "FileHashDetails.json").name}"'}
        with open(files_delta_store_folder_path_object / 'FileHashDetails.json', 'r', encoding = 'utf-8') as file_hash_details_file_object:
            file_hash_json_data_from_blob = json.load(file_hash_details_file_object)
        print(f'{"[INFO]":<10} File Hash Details From BLOB Loaded: "{(files_delta_store_folder_path_object / "FileHashDetails.json").name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '5', 'message': str(error)}

    # Load JSON Dump File From Local:S6
    try:
        json_dump_file_path_object = Path(json_dump_file_path)
        if not json_dump_file_path_object.exists() or not json_dump_file_path_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '6', 'message': f'JSON Dump File From Local Not Found Or Not A File: "{Path(json_dump_file_path).name}"'}
        with open(json_dump_file_path_object, 'r', encoding = 'utf-8') as json_dump_file_object:
            json_dump_json_data_from_local = json.load(json_dump_file_object)
        print(f'{"[INFO]":<10} JSON Dump File From Local Loaded: "{json_dump_file_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '6', 'message': str(error)}

    # Compare File Hash Details From BLOB With JSON Dump From Local:S7
    try:
        if file_hash_json_data_from_blob == json_dump_json_data_from_local:
            print(f'{"[INFO]":<10} File Hash Details From BLOB Matches JSON Dump From Local')
        else:
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '7', 'message': 'File Hash Details From BLOB Does Not Match JSON Dump From Local'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '7', 'message': str(error)}

    # Clear All Files From Azure BLOB Container Including FileHashDetails.json:S8
    try:
        clear_blobs_result = files_clear_from_blob(
            env_file_path = env_file_path,
            hash_file_delete = True
        )
        if clear_blobs_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '8', 'message': f'Failed To Clear All Files From Azure BLOB: {clear_blobs_result.get("message")}'}
        print(f'{"[INFO]":<10} All Files Cleared From Azure BLOB Container Including FileHashDetails.json')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '8', 'message': str(error)}

    # Update Local File Details - Detection And Staging:S9
    try:
        local_update_result = local_file_details_update(
            database_file_path = database_file_path,
            json_dump_file_path = json_dump_file_path,
            analysis_engine_folder_path = analysis_engine_folder_path,
            files_delta_store_folder_path = files_delta_store_folder_path
        )
        if local_update_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '9', 'message': f'Failed To Update Local File Details: {local_update_result.get("message")}'}
        files_to_upload_list = local_update_result.get('files_to_upload_list', [])
        added_file_hash_details_dict = local_update_result.get('added_file_hash_details_dict', {})
        modified_file_hash_details_dict = local_update_result.get('modified_file_hash_details_dict', {})
        deleted_file_hash_details_dict = local_update_result.get('deleted_file_hash_details_dict', {})
        print(f'{"[INFO]":<10} Local File Details Detection Completed')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '9', 'message': str(error)}

    # Upload Files To Azure BLOB Container:S10
    try:
        print(f'{"[INFO]":<10} Total Files Ready For Upload To Azure BLOB: {len(files_to_upload_list)}')
        for upload_file_path in files_to_upload_list:
            upload_result = file_upload_to_blob(env_file_path = env_file_path, upload_file_path = upload_file_path, blobs_delete = False)
            if upload_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '10', 'message': f'Failed To Upload File "{Path(upload_file_path).name}": {upload_result.get("message")}'}
        print(f'{"[INFO]":<10} Total Files Uploaded To Azure BLOB: {len(files_to_upload_list)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '10', 'message': str(error)}

    # Upload JSON Dump File To Azure BLOB Container:S11
    try:
        json_upload_result = file_upload_to_blob(env_file_path = env_file_path, upload_file_path = json_dump_file_path, blobs_delete = False)
        if json_upload_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '11', 'message': f'Failed To Upload JSON Dump File: {json_upload_result.get("message")}'}
        print(f'{"[INFO]":<10} JSON Dump File Uploaded To Azure BLOB: "{Path(json_dump_file_path).name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '11', 'message': str(error)}

    # Persist Local File Details After Successful Upload:S12
    try:
        persist_result = persist_file_details_update(
            database_file_path = database_file_path,
            json_dump_file_path = json_dump_file_path,
            added_file_hash_details_dict = added_file_hash_details_dict,
            modified_file_hash_details_dict = modified_file_hash_details_dict,
            deleted_file_hash_details_dict = deleted_file_hash_details_dict
        )
        if persist_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '12', 'message': f'Failed To Persist Local File Details: {persist_result.get("message")}'}
        print(f'{"[INFO]":<10} Local File Details Persisted Successfully')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '12', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Upload-Files-Delta', 'step': '12', 'message': 'Upload Files Delta Completed Successfully'}
