# Define "upload_files_delta" Function
def upload_files_delta(env_file_path: str, database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, str]: #type: ignore
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import shutil
        import json
        import sqlite3
        import hashlib
        from datetime import datetime
        from supportscript.blobfilesoperation import blob_files_operation
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
        download_result = blob_files_operation(
            operation = 'download',
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
        clear_blobs_result = blob_files_operation(
            operation = 'clear',
            env_file_path = env_file_path,
            hash_file_delete = True
        )
        if clear_blobs_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '8', 'message': f'Failed To Clear All Files From Azure BLOB: {clear_blobs_result.get("message")}'}
        print(f'{"[INFO]":<10} All Files Cleared From Azure BLOB Container Including FileHashDetails.json')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '8', 'message': str(error)}

    # Connect To Analysis File Hash Database And Fetch Existing Hashes:S9
    try:
        database_file_object = Path(database_file_path)
        database_connection = sqlite3.connect(str(database_file_object))
        database_cursor = database_connection.cursor()
        database_cursor.execute('SELECT file_path, file_md5_hash, file_size_in_bytes, file_uploaded_at, file_updated_at, file_status FROM analysis_file_hash')
        database_file_full_details_dict = {
            row[0]: {
                'file_hash_value': row[1],
                'file_size_in_bytes': row[2],
                'file_uploaded_at': row[3],
                'file_updated_at': row[4],
                'file_status': row[5]
            }
            for row in database_cursor.fetchall()
        }
        database_connection.close()
        print(f'{"[INFO]":<10} Analysis File Hash Database Connected At: "{database_file_object.name}"')
        print(f'{"[INFO]":<10} Total File Hash Records Fetched: {len(database_file_full_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '9', 'message': str(error)}

    # Load JSON Dump File And Extract File Hashes:S10
    try:
        json_dump_file_object = Path(json_dump_file_path)
        with open(json_dump_file_object, 'r', encoding = 'utf-8') as json_file:
            json_dump_data = json.load(json_file)
        json_file_hash_details_dict = {file_path: file_hash_details['file_hash_value'] for file_path, file_hash_details in json_dump_data.items()}
        print(f'{"[INFO]":<10} JSON Dump File Loaded: "{json_dump_file_object.name}"')
        print(f'{"[INFO]":<10} Total JSON File Hash Records Fetched: {len(json_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '10', 'message': str(error)}

    # Compare Database And JSON File Hashes:S11
    try:
        database_file_hash_details_dict = {file_path: file_details['file_hash_value'] for file_path, file_details in database_file_full_details_dict.items()}
        if database_file_hash_details_dict == json_file_hash_details_dict:
            final_file_hash_details_dict = database_file_hash_details_dict.copy()
            print(f'{"[INFO]":<10} Database And JSON File Hashes Matched Perfectly')
            print(f'{"[INFO]":<10} Total Final File Hash Records: {len(final_file_hash_details_dict)}')
        else:
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '11', 'message': 'Database And JSON File Hashes Do Not Match'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '11', 'message': str(error)}

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
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '12', 'message': 'Analysis Engine Folder Does Not Exist Or Is Not Directory'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '12', 'message': str(error)}

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
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '13', 'message': str(error)}

    # Identify Added Files From Current File Hashes:S14
    try:
        added_file_hash_details_dict = {}
        files_to_upload_list = []
        for file_path, file_details in current_file_hash_details_dict.items():
            if file_path not in final_file_hash_details_dict:
                added_file_hash_details_dict[file_path] = {
                    'file_hash_value': file_details['file_hash_value'],
                    'file_size_in_bytes': file_details['file_size_in_bytes'],
                    'file_uploaded_at': file_details['file_uploaded_at'],
                    'file_updated_at': file_details['file_updated_at'],
                    'file_status': 'Added'
                }
        print(f'{"[INFO]":<10} Total Added File Hash Records Identified: {len(added_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '14', 'message': str(error)}

    # Identify Modified Files From Current File Hashes:S15
    try:
        modified_file_hash_details_dict = {}
        for file_path, file_details in current_file_hash_details_dict.items():
            final_file_hash = final_file_hash_details_dict.get(file_path)
            if final_file_hash is not None and file_details.get('file_hash_value') != final_file_hash:
                old_file_details = database_file_full_details_dict.get(file_path, {})
                modified_file_hash_details_dict[file_path] = {
                    'file_hash_value': file_details['file_hash_value'],
                    'file_size_in_bytes': file_details['file_size_in_bytes'],
                    'file_uploaded_at': old_file_details.get('file_uploaded_at', file_details['file_uploaded_at']),
                    'file_updated_at': file_details['file_updated_at'],
                    'file_status': 'Modified'
                }
        print(f'{"[INFO]":<10} Total Modified File Hash Records Identified: {len(modified_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '15', 'message': str(error)}

    # Identify Deleted Files From Final File Hashes:S16
    try:
        deleted_file_hash_details_dict = {}
        for file_path in final_file_hash_details_dict:
            if file_path not in current_file_hash_details_dict:
                old_file_details = database_file_full_details_dict.get(file_path, {})
                deleted_file_hash_details_dict[file_path] = {
                    'file_hash_value': old_file_details.get('file_hash_value', 'unknown'),
                    'file_size_in_bytes': old_file_details.get('file_size_in_bytes', 0),
                    'file_status': 'Deleted',
                    'file_uploaded_at': old_file_details.get('file_uploaded_at', datetime.now().isoformat()),
                    'file_updated_at': datetime.now().isoformat()
                }
        print(f'{"[INFO]":<10} Total Deleted File Hash Records Identified: {len(deleted_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '16', 'message': str(error)}

    # Copy Added Files To FilesDelta Folder:S17
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        added_files_copied_count = 0
        for relative_file_path in added_file_hash_details_dict:
            destination_file_path_object = files_delta_store_folder_path_object / relative_file_path
            destination_file_path_object.parent.mkdir(parents = True, exist_ok = True)
            shutil.copy2(str(Path(analysis_engine_folder_path) / relative_file_path), str(destination_file_path_object))
            files_to_upload_list.append(str(destination_file_path_object))
            added_files_copied_count += 1
        print(f'{"[INFO]":<10} Total Added Files Copied To Upload Folder: {added_files_copied_count}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '17', 'message': str(error)}

    # Copy Modified Files To FilesDelta Folder:S18
    try:
        modified_files_copied_count = 0
        for relative_file_path in modified_file_hash_details_dict:
            destination_file_path_object = files_delta_store_folder_path_object / relative_file_path
            destination_file_path_object.parent.mkdir(parents = True, exist_ok = True)
            shutil.copy2(str(Path(analysis_engine_folder_path) / relative_file_path), str(destination_file_path_object))
            files_to_upload_list.append(str(destination_file_path_object))
            modified_files_copied_count += 1
        print(f'{"[INFO]":<10} Total Modified Files Copied To Upload Folder: {modified_files_copied_count}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '18', 'message': str(error)}

    # Upload Files To Azure BLOB Container:S19
    try:
        print(f'{"[INFO]":<10} Total Files Ready For Upload To Azure BLOB: {len(files_to_upload_list)}')
        for upload_file_path in files_to_upload_list:
            upload_result = blob_files_operation(
                operation = 'upload',
                env_file_path = env_file_path,
                upload_file_path = upload_file_path
            )
            if upload_result.get('status') != 'SUCCESS':
                return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '19', 'message': f'Failed To Upload File "{Path(upload_file_path).name}": {upload_result.get("message")}'}
        print(f'{"[INFO]":<10} Total Files Uploaded To Azure BLOB: {len(files_to_upload_list)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '19', 'message': str(error)}

    # Update JSON Dump File With Added, Modified And Deleted File Details:S20
    try:
        with open(json_dump_file_path, 'r', encoding = 'utf-8') as json_file:
            json_dump_data = json.load(json_file)
        json_dump_data.update(added_file_hash_details_dict)
        json_dump_data.update(modified_file_hash_details_dict)
        json_dump_data.update(deleted_file_hash_details_dict)
        with open(json_dump_file_path, 'w', encoding = 'utf-8') as json_file:
            json.dump(json_dump_data, json_file, indent = 2)
        print(f'{"[INFO]":<10} JSON Dump File Updated With Added, Modified And Deleted File Details: "{Path(json_dump_file_path).name}"')
        print(f'{"[INFO]":<10} Total Added File Details Updated In JSON Dump File: {len(added_file_hash_details_dict)}')
        print(f'{"[INFO]":<10} Total Modified File Details Updated In JSON Dump File: {len(modified_file_hash_details_dict)}')
        print(f'{"[INFO]":<10} Total Deleted File Details Updated In JSON Dump File: {len(deleted_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '20', 'message': str(error)}

    # Upload JSON Dump File To Azure BLOB Container:S21
    try:
        json_upload_result = blob_files_operation(
            operation = 'upload',
            env_file_path = env_file_path,
            upload_file_path = json_dump_file_path
        )
        if json_upload_result.get('status') != 'SUCCESS':
            return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '21', 'message': f'Failed To Upload JSON Dump File: {json_upload_result.get("message")}'}
        print(f'{"[INFO]":<10} JSON Dump File Uploaded To Azure BLOB: "{Path(json_dump_file_path).name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '21', 'message': str(error)}

    # Insert Or Update Added File Details Into Database:S22
    try:
        database_connection = sqlite3.connect(database_file_path)
        database_cursor = database_connection.cursor()
        total_added_upserted = 0
        for file_path, file_hash_details in added_file_hash_details_dict.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_added_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Added File Details Upserted Into Database: {total_added_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '22', 'message': str(error)}

    # Insert Or Update Modified File Details Into Database:S23
    try:
        database_connection = sqlite3.connect(database_file_path)
        database_cursor = database_connection.cursor()
        total_modified_upserted = 0
        for file_path, file_hash_details in modified_file_hash_details_dict.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_modified_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Modified File Details Upserted Into Database: {total_modified_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '23', 'message': str(error)}

    # Insert Or Update Deleted File Details Into Database:S24
    try:
        database_connection = sqlite3.connect(database_file_path)
        database_cursor = database_connection.cursor()
        total_deleted_upserted = 0
        for file_path, file_hash_details in deleted_file_hash_details_dict.items():
            database_cursor.execute('''
                INSERT OR REPLACE INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_size_in_bytes, file_status, file_updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_size_in_bytes'], file_hash_details['file_status'], file_hash_details['file_updated_at']))
            total_deleted_upserted += 1
        database_connection.commit()
        database_connection.close()
        print(f'{"[INFO]":<10} Total Deleted File Details Upserted Into Database: {total_deleted_upserted}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '24', 'message': str(error)}

    # Delete And Recreate FilesDelta Folder:S25
    try:
        files_delta_store_folder_path_object = Path(files_delta_store_folder_path)
        if files_delta_store_folder_path_object.exists():
            shutil.rmtree(str(files_delta_store_folder_path_object))
        files_delta_store_folder_path_object.mkdir(parents = True, exist_ok = True)
        print(f'{"[INFO]":<10} FilesDelta Folder Deleted And Recreated: "{files_delta_store_folder_path_object.name}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Upload-Files-Delta', 'step': '25', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Upload-Files-Delta', 'step': '25', 'message': 'Upload Files Delta Completed Successfully'}