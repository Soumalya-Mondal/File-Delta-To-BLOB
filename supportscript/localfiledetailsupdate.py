# Define "local_file_details_update" Function
from typing import Any
def local_file_details_update(database_file_path: str, json_dump_file_path: str, analysis_engine_folder_path: str, files_delta_store_folder_path: str) -> dict[str, Any]:
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import sqlite3
        import json
        import hashlib
        from datetime import datetime
        import shutil
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '1', 'message': str(error)}

    # Connect To Analysis File Hash Database And Fetch Existing Hashes:S2
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '2', 'message': str(error)}

    # Load JSON Dump File And Extract File Hashes:S3
    try:
        json_dump_file_object = Path(json_dump_file_path)
        with open(json_dump_file_object, 'r', encoding = 'utf-8') as json_file:
            json_dump_data = json.load(json_file)
        json_file_hash_details_dict = {file_path: file_hash_details['file_hash_value'] for file_path, file_hash_details in json_dump_data.items()}
        print(f'{"[INFO]":<10} JSON Dump File Loaded: "{json_dump_file_object.name}"')
        print(f'{"[INFO]":<10} Total JSON File Hash Records Fetched: {len(json_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '3', 'message': str(error)}

    # Compare Database And JSON File Hashes:S4
    try:
        database_file_hash_details_dict = {file_path: file_details['file_hash_value'] for file_path, file_details in database_file_full_details_dict.items()}
        if database_file_hash_details_dict == json_file_hash_details_dict:
            final_file_hash_details_dict = database_file_hash_details_dict.copy()
            print(f'{"[INFO]":<10} Database And JSON File Hashes Matched Perfectly')
            print(f'{"[INFO]":<10} Total Final File Hash Records: {len(final_file_hash_details_dict)}')
        else:
            return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '4', 'message': 'Database And JSON File Hashes Do Not Match'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '4', 'message': str(error)}

    # Collect All Files From Analysis Engine:S5
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
            return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '5', 'message': 'Analysis Engine Folder Does Not Exist Or Is Not Directory'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '5', 'message': str(error)}

    # Calculate MD5 Hash For All Collected Files:S6
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '6', 'message': str(error)}

    # Identify Added Files From Current File Hashes:S7
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '7', 'message': str(error)}

    # Identify Modified Files From Current File Hashes:S8
    try:
        modified_file_hash_details_dict = {}
        for file_path, file_details in current_file_hash_details_dict.items():
            final_file_hash = final_file_hash_details_dict.get(file_path)
            if final_file_hash is not None and file_details.get('file_hash_value') != final_file_hash:
                modified_file_hash_details_dict[file_path] = {
                    'file_hash_value': file_details['file_hash_value'],
                    'file_size_in_bytes': file_details['file_size_in_bytes'],
                    'file_uploaded_at': file_details['file_uploaded_at'],
                    'file_updated_at': file_details['file_updated_at'],
                    'file_status': 'Modified'
                }
        print(f'{"[INFO]":<10} Total Modified File Hash Records Identified: {len(modified_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '8', 'message': str(error)}

    # Identify Deleted Files From Final File Hashes:S9
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '9', 'message': str(error)}

    # Copy Added Files To FilesDelta Folder:S10
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '10', 'message': str(error)}

    # Copy Modified Files To FilesDelta Folder:S11
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '11', 'message': str(error)}

    # Insert Or Update Added File Details Into Database:S12
    try:
        database_connection = sqlite3.connect(str(database_file_object))
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '12', 'message': str(error)}

    # Insert Or Update Modified File Details Into Database:S13
    try:
        database_connection = sqlite3.connect(str(database_file_object))
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '13', 'message': str(error)}

    # Insert Or Update Deleted File Details Into Database:S14
    try:
        database_connection = sqlite3.connect(str(database_file_object))
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
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '14', 'message': str(error)}

    # Update JSON Dump File With Added, Modified And Deleted File Details:S15
    try:
        with open(json_dump_file_object, 'r', encoding = 'utf-8') as json_file:
            json_dump_data = json.load(json_file)
        json_dump_data.update(added_file_hash_details_dict)
        json_dump_data.update(modified_file_hash_details_dict)
        json_dump_data.update(deleted_file_hash_details_dict)
        with open(json_dump_file_object, 'w', encoding = 'utf-8') as json_file:
            json.dump(json_dump_data, json_file, indent = 2)
        print(f'{"[INFO]":<10} JSON Dump File Updated With Added, Modified And Deleted File Details: "{json_dump_file_object.name}"')
        print(f'{"[INFO]":<10} Total Added File Details Updated In JSON Dump File: {len(added_file_hash_details_dict)}')
        print(f'{"[INFO]":<10} Total Modified File Details Updated In JSON Dump File: {len(modified_file_hash_details_dict)}')
        print(f'{"[INFO]":<10} Total Deleted File Details Updated In JSON Dump File: {len(deleted_file_hash_details_dict)}')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Details-Update', 'step': '15', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Local-File-Details-Update', 'step': '15', 'message': 'Local File Details Updated Successfully', 'files_to_upload_list': files_to_upload_list}
