# Define "file_details_compare" Function
def file_details_compare(env_file_path: str, files_delta_store_folder_path: str, json_dump_file_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        import json
        from supportscript.filedownloadfromblob import file_download_from_blob
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '1', 'message': str(error)}

    # Delete And Recreate FilesDelta Folder:S2
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Folder Deleted And Recreated: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '2', 'message': str(error)}

    # Download File Hash Details From Azure BLOB Container:S3
    try:
        download_result = file_download_from_blob(
            env_file_path = env_file_path,
            files_delta_store_folder_path = files_delta_store_folder_path,
            file_hash_download = True
        )
        if download_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '3', 'message': f'Failed To Download File Hash Details From Azure BLOB: {download_result.get("message")}'}
        print(f'{"[INFO]":<10} File Hash Details Downloaded From Azure BLOB')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '3', 'message': str(error)}

    # Load File Hash Details JSON File From BLOB:S4
    try:
        if not files_delta_store_folder_path_object.exists() or not files_delta_store_folder_path_object.is_dir():
            return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '4', 'message': f'FilesDelta Folder Not Found Or Not A Directory: {files_delta_store_folder_path}'}
        if not (files_delta_store_folder_path_object / 'FileHashDetails.json').exists() or not (files_delta_store_folder_path_object / 'FileHashDetails.json').is_file():
            return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '4', 'message': f'FileHashDetails.json From BLOB Not Found Or Not A File: {files_delta_store_folder_path_object / "FileHashDetails.json"}'}
        with open(files_delta_store_folder_path_object / 'FileHashDetails.json', 'r', encoding = 'utf-8') as file_hash_details_file_object:
            file_hash_json_data_from_blob = json.load(file_hash_details_file_object)
        print(f'{"[INFO]":<10} File Hash Details From BLOB Loaded: "{(files_delta_store_folder_path_object / "FileHashDetails.json").name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '4', 'message': str(error)}

    # Load JSON Dump File From Local:S5
    try:
        json_dump_file_path_object = Path(json_dump_file_path)
        if not json_dump_file_path_object.exists() or not json_dump_file_path_object.is_file():
            return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '5', 'message': f'JSON Dump File From Local Not Found Or Not A File: {json_dump_file_path}'}
        with open(json_dump_file_path_object, 'r', encoding = 'utf-8') as json_dump_file_object:
            json_dump_json_data_from_local = json.load(json_dump_file_object)
        print(f'{"[INFO]":<10} JSON Dump File From Local Loaded: "{json_dump_file_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '5', 'message': str(error)}

    # Compare File Hash Details From BLOB With JSON Dump From Local:S6
    try:
        if file_hash_json_data_from_blob == json_dump_json_data_from_local:
            return {'status': 'SUCCESS', 'script_name': 'File-Details-Compare', 'step': '6', 'message': 'File Hash Details From BLOB Matches JSON Dump From Local'}
        else:
            return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '6', 'message': 'File Hash Details From BLOB Does Not Match JSON Dump From Local'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'File-Details-Compare', 'step': '6', 'message': str(error)}
