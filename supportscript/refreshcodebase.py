# Define "refresh_code_base" Function
def refresh_code_base(env_file_path: str, database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        from supportscript.localfiledetailsupdate import local_file_details_update
        from supportscript.fileuploadtoblob import file_upload_to_blob
        from supportscript.filedetailscompare import file_details_compare
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '1', 'message': str(error)}

    # Check Env, Database And JSON File Present:S2
    try:
        env_file_object = Path(env_file_path)
        if not env_file_object.exists() or not env_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '2', 'message': f'Environment file not found or not a file: {env_file_path}'}

        database_file_object = Path(database_file_path)
        if not database_file_object.exists() or not database_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '2', 'message': f'Database file not found or not a file: {database_file_path}'}

        json_dump_file_object = Path(json_dump_file_path)
        if not json_dump_file_object.exists() or not json_dump_file_object.is_file():
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '2', 'message': f'JSON dump file not found or not a file: {json_dump_file_path}'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '2', 'message': str(error)}

    # Delete And Recreate FilesDelta Folder:S3
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Folder Deleted And Recreated: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '3', 'message': str(error)}

    # Compare File Details With BLOB:S4
    try:
        file_details_compare_result = file_details_compare(
            env_file_path = env_file_path,
            files_delta_store_folder_path = files_delta_store_folder_path,
            json_dump_file_path = json_dump_file_path
        )
        if file_details_compare_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '4', 'message': f'Failed To Compare File Details: {file_details_compare_result.get("message")}'}
        print(f'{"[INFO]":<10} File Details Compared Successfully')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '4', 'message': str(error)}

    # Update Local File Details:S5
    try:
        local_update_result = local_file_details_update(
            database_file_path = database_file_path,
            json_dump_file_path = json_dump_file_path,
            analysis_engine_folder_path = analysis_engine_folder_path,
            files_delta_store_folder_path = files_delta_store_folder_path
        )
        if local_update_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '5', 'message': f'Failed To Update Local File Details: {local_update_result.get("message")}'}
        files_to_upload_list = local_update_result.get('files_to_upload_list', [])
        print(f'{"[INFO]":<10} Local File Details Updated')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '5', 'message': str(error)}

    # Upload Files To Azure BLOB Container:S6
    try:
        print(f'{"[INFO]":<10} Total Files Ready For Upload To Azure BLOB: {len(files_to_upload_list)}')
        for upload_file_path in files_to_upload_list:
            upload_result = file_upload_to_blob(env_file_path = env_file_path, upload_file_path = upload_file_path)
            if upload_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '6', 'message': f'Failed To Upload File "{upload_file_path}": {upload_result.get("message")}'}
        print(f'{"[INFO]":<10} Total Files Uploaded To Azure BLOB: {len(files_to_upload_list)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '6', 'message': str(error)}

    # Upload JSON Dump File To Azure BLOB Container:S7
    try:
        json_upload_result = file_upload_to_blob(env_file_path = env_file_path, upload_file_path = json_dump_file_path)
        if json_upload_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '7', 'message': f'Failed To Upload JSON Dump File: {json_upload_result.get("message")}'}
        print(f'{"[INFO]":<10} JSON Dump File Uploaded To Azure BLOB: "{Path(json_dump_file_path).name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Refresh-Code-Base', 'step': '7', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Refresh-Code-Base', 'step': '7', 'message': 'Refresh code base completed successfully'}
