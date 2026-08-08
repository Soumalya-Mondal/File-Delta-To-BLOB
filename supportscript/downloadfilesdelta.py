# Define "download_files_delta" Function
def download_files_delta(env_file_path: str, database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        import json
        import hashlib
        import sqlite3
        from datetime import datetime
        from supportscript.blobfilesoperation import blob_files_operation
        from supportscript.localfileprocess import local_file_process
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
        file_hash_download_result = blob_files_operation(
            operation = 'download',
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
                add_files_details[file_path]['file_status'] = 'Added'
            else:
                # File exists in both -> check if hash changed
                if blob_file_details.get('file_hash_value') != local_file_details.get('file_hash_value'):
                    modified_files_details[file_path] = dict(blob_file_details)
                    modified_files_details[file_path]['file_status'] = 'Modified'
                    modified_files_details[file_path]['file_uploaded_at'] = local_file_details.get('file_uploaded_at', blob_file_details.get('file_uploaded_at'))

        # Identify Deleted Files From Local (not in BLOB)
        for file_path, local_file_details in local_file_hash_details_json_object.items():
            if file_path not in blob_file_hash_details_json_object:
                delete_files_details[file_path] = dict(local_file_details)
                delete_files_details[file_path]['file_status'] = 'Deleted'

        print(f'{"[INFO]":<10} Total Added Files Details Created: {len(add_files_details)}')
        print(f'{"[INFO]":<10} Total Modified Files Details Created: {len(modified_files_details)}')
        print(f'{"[INFO]":<10} Total Deleted Files Details Created: {len(delete_files_details)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '7', 'message': str(error)}

    # Download Actual Files From Azure BLOB:S8
    try:
        file_download_result = blob_files_operation(
            operation = 'download',
            env_file_path = env_file_path,
            files_delta_store_folder_path = files_delta_store_folder_path,
            file_hash_download = False
        )
        if file_download_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '8', 'message': f'Failed To Download Actual Files: {file_download_result.get("message")}'}
        print(f'{"[INFO]":<10} Actual Files Downloaded From Azure BLOB')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '8', 'message': str(error)}

    # Process Added Files:S9
    try:
        for file_path, _ in add_files_details.items():
            add_process_result = local_file_process(
                files_delta_store_folder_path = files_delta_store_folder_path,
                analysis_engine_folder_path = str(analysis_engine_folder_path),
                file_path = file_path,
                job_type = 'add'
            )
            if add_process_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '9', 'message': f'Failed To Process Added File "{file_path}": {add_process_result.get("message")}'}
        print(f'{"[INFO]":<10} All Added Files Processed Successfully: Total="{len(add_files_details)}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '9', 'message': str(error)}

    # Process Modified Files:S10
    try:
        for file_path, _ in modified_files_details.items():
            modified_process_result = local_file_process(
                files_delta_store_folder_path = files_delta_store_folder_path,
                analysis_engine_folder_path = str(analysis_engine_folder_path),
                file_path = file_path,
                job_type = 'modified'
            )
            if modified_process_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '10', 'message': f'Failed To Process Modified File "{file_path}": {modified_process_result.get("message")}'}
        print(f'{"[INFO]":<10} All Modified Files Processed Successfully: Total="{len(modified_files_details)}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '10', 'message': str(error)}

    # Process Deleted Files:S11
    try:
        for file_path, _ in delete_files_details.items():
            delete_process_result = local_file_process(
                files_delta_store_folder_path = files_delta_store_folder_path,
                analysis_engine_folder_path = str(analysis_engine_folder_path),
                file_path = file_path,
                job_type = 'delete'
            )
            if delete_process_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '11', 'message': f'Failed To Process Deleted File "{file_path}": {delete_process_result.get("message")}'}
        print(f'{"[INFO]":<10} All Deleted Files Processed Successfully: Total="{len(delete_files_details)}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '11', 'message': str(error)}

    # Collect All Files From Analysis Engine:S12
    try:
        analysis_engine_files_path_list = []
        exclude_folder_list = ['node_modules', '__pycache__', '.git', '.venv']
        exclude_file_list = ['package-lock.json', '.gitattributes', '.gitignore', '.python-version', '.env', 'uv.lock']
        analysis_engine_folder_path_object = Path(analysis_engine_folder_path)
        if analysis_engine_folder_path_object.exists() and analysis_engine_folder_path_object.is_dir():
            for file_path in analysis_engine_folder_path_object.rglob('*'):
                if any(exclude_folder in file_path.parts for exclude_folder in exclude_folder_list):
                    continue
                if file_path.is_file() and file_path.name in exclude_file_list:
                    continue
                if file_path.is_file():
                    analysis_engine_files_path_list.append(file_path)
            print(f'{"[INFO]":<10} Total Files Collected From Source Folder: {len(analysis_engine_files_path_list)}')
        else:
            return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '12', 'message': 'Analysis Engine Folder Does Not Exist Or Is Not Directory'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '12', 'message': str(error)}

    # Calculate MD5 Hash For All Collected Files:S13
    try:
        current_file_hash_details_dict = {}
        for file_path in analysis_engine_files_path_list:
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    md5_hash.update(chunk)
            current_file_hash_details_dict[str(file_path.relative_to(analysis_engine_folder_path_object))] = {
                'file_hash_value': md5_hash.hexdigest(),
                'file_size_in_bytes': file_path.stat().st_size,
                'file_uploaded_at': (timestamp := datetime.now().isoformat()),
                'file_updated_at': timestamp
            }
        print(f'{"[INFO]":<10} Total MD5 Hashes Calculated: {len(current_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '13', 'message': str(error)}

    # Compare BLOB File Hash Details With Current Analysis Engine File Hash Details And Initialize Updated Local Dictionary:S14
    try:
        updated_local_file_hash_details_dict = dict(local_file_hash_details_json_object)

        for file_path, blob_file_details in blob_file_hash_details_json_object.items():
            current_file_details = current_file_hash_details_dict.get(file_path)
            if current_file_details is None:
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '14', 'message': f'File Present In BLOB But Missing In Analysis Engine: "{Path(file_path).name}"'}
            if blob_file_details.get('file_hash_value') != current_file_details.get('file_hash_value'):
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '14', 'message': f'File Hash Mismatch Detected For File: "{Path(file_path).name}" BLOB="{blob_file_details.get("file_hash_value")}" Local="{current_file_details.get("file_hash_value")}"'}

        for file_path, current_file_details in current_file_hash_details_dict.items():
            if file_path not in blob_file_hash_details_json_object:
                return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '14', 'message': f'File Present In Analysis Engine But Missing In BLOB: "{Path(file_path).name}"'}

        print(f'{"[INFO]":<10} BLOB File Hash Details Verified Against Analysis Engine Files Successfully')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '14', 'message': str(error)}

    # Update Added File Details In Local JSON:S15
    try:
        for file_path, file_details in add_files_details.items():
            updated_local_file_hash_details_dict[file_path] = {
                'file_hash_value': file_details['file_hash_value'],
                'file_size_in_bytes': file_details['file_size_in_bytes'],
                'file_status': 'Added',
                'file_uploaded_at': file_details['file_uploaded_at'],
                'file_updated_at': file_details['file_updated_at']
            }
        print(f'{"[INFO]":<10} Total Added File Details Updated In JSON Dump File: {len(add_files_details)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '15', 'message': str(error)}

    # Update Modified File Details In Local JSON:S16
    try:
        for file_path, file_details in modified_files_details.items():
            old_local_file_details = local_file_hash_details_json_object.get(file_path, {})
            updated_local_file_hash_details_dict[file_path] = {
                'file_hash_value': file_details['file_hash_value'],
                'file_size_in_bytes': file_details['file_size_in_bytes'],
                'file_status': 'Modified',
                'file_uploaded_at': old_local_file_details.get('file_uploaded_at', file_details['file_uploaded_at']),
                'file_updated_at': file_details['file_updated_at']
            }
        print(f'{"[INFO]":<10} Total Modified File Details Updated In JSON Dump File: {len(modified_files_details)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '16', 'message': str(error)}

    # Update Deleted File Details In Local JSON:S17
    try:
        for file_path, file_details in delete_files_details.items():
            updated_local_file_hash_details_dict[file_path] = {
                'file_hash_value': file_details['file_hash_value'],
                'file_size_in_bytes': file_details['file_size_in_bytes'],
                'file_status': 'Deleted',
                'file_uploaded_at': file_details['file_uploaded_at'],
                'file_updated_at': file_details['file_updated_at']
            }
        print(f'{"[INFO]":<10} Total Deleted File Details Updated In JSON Dump File: {len(delete_files_details)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '17', 'message': str(error)}

    # Write Updated File Hash Details To Local JSON:S18
    try:
        with open(json_dump_file_path, 'w', encoding = 'utf-8') as json_file:
            json.dump(updated_local_file_hash_details_dict, json_file, indent = 2)
        print(f'{"[INFO]":<10} Local File Hash Details JSON Updated Successfully: "{Path(json_dump_file_path).name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '18', 'message': str(error)}

    # Insert Or Update Added File Details Into Database:S19
    try:
        database_connection = sqlite3.connect(str(database_file_path))
        database_cursor = database_connection.cursor()
        total_added_upserted = 0
        for file_path, file_hash_details in add_files_details.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_added_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Added File Details Upserted Into Database: {total_added_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '19', 'message': str(error)}

    # Insert Or Update Modified File Details Into Database:S20
    try:
        database_connection = sqlite3.connect(str(database_file_path))
        database_cursor = database_connection.cursor()
        total_modified_upserted = 0
        for file_path, file_hash_details in modified_files_details.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_modified_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Modified File Details Upserted Into Database: {total_modified_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '20', 'message': str(error)}

    # Insert Or Update Deleted File Details Into Database:S21
    try:
        database_connection = sqlite3.connect(str(database_file_path))
        database_cursor = database_connection.cursor()
        total_deleted_upserted = 0
        for file_path, file_hash_details in delete_files_details.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_deleted_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Deleted File Details Upserted Into Database: {total_deleted_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '21', 'message': str(error)}

    # Clear FilesDelta Store Folder:S22
    try:
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Store Folder Cleared: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Download-Files-Delta', 'step': '22', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Download-Files-Delta', 'step': '22', 'message': 'Download Files Delta Completed Successfully'}
