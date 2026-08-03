# Define Main Function
if __name__ == '__main__':
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import sqlite3
        import hashlib
        import json
        from datetime import datetime
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S1] - {str(error)}')

    # Define Folder Path:S2
    try:
        parent_folder_path = Path.cwd()
        env_file_path = Path(parent_folder_path) / '.env'
        file_upload_folder_path = Path(parent_folder_path) / 'FileUpload'
        file_upload_folder_path.mkdir(parents = True, exist_ok = True)
        file_download_folder_path = Path(parent_folder_path) / 'FileDownload'
        file_download_folder_path.mkdir(parents = True, exist_ok = True)
        database_folder_path = Path(parent_folder_path) / 'database'
        database_folder_path.mkdir(parents = True, exist_ok = True)
        file_hash_details_json_path = Path(parent_folder_path) / 'FileHashDetails.json'
        analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S2] - {str(error)}')

    # Create Analysis File Hash Database:S3
    try:
        database_file_path = Path(database_folder_path) / 'AnalysisFileHash.db'
        database_connection = sqlite3.connect(str(database_file_path))
        database_connection.close()
        print(f'INFO - Analysis File Hash Database Created At: {database_file_path}')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S3] - {str(error)}')

    # Create Analysis File Hash Table:S4
    try:
        if database_file_path.exists():
            database_connection = sqlite3.connect(str(database_file_path))
            database_cursor = database_connection.cursor()
            database_cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_file_hash (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_uploaded_at DATETIME NOT NULL,
                    file_path TEXT UNIQUE NOT NULL,
                    file_md5_hash TEXT NOT NULL,
                    file_updated_at DATETIME NOT NULL
                )
            ''')
            database_connection.commit()
            database_connection.close()
            print(f'INFO - Analysis File Hash Table Verified In Database')
        else:
            print(f'ERROR - [File-Delta-To-BLOB:S4] - Analysis File Hash Database File Not Found')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S4] - {str(error)}')

    # Collect All Files From Analysis Engine:S5
    try:
        analysis_engine_files_path_list = []
        exclude_folder_list = ['node_modules', '__pycache__', '.git', '.venv']
        exclude_file_list = ['package-lock.json', '.gitattributes', '.gitignore', '.python-version', '.env', 'uv.lock']
        if analysis_engine_folder_path.exists() and analysis_engine_folder_path.is_dir():
            for file_path in analysis_engine_folder_path.rglob('*'):
                if any(exclude_folder in file_path.parts for exclude_folder in exclude_folder_list):
                    continue
                if file_path.is_file() and file_path.name in exclude_file_list:
                    continue
                if file_path.is_file():
                    analysis_engine_files_path_list.append(file_path)
            print(f'INFO - Total Files Collected From Analysis Engine: {len(analysis_engine_files_path_list)}')
        else:
            print(f'ERROR - [File-Delta-To-BLOB:S5] - Analysis Engine Folder Does Not Exist Or Is Not Directory')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S5] - {str(error)}')

    # Calculate MD5 Hash For All Collected Files:S6
    try:
        file_hash_details_dict = {}
        for file_path in analysis_engine_files_path_list:
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    md5_hash.update(chunk)
            file_hash_details_dict[str(file_path.relative_to(analysis_engine_folder_path))] = {
                'file_hash_value': md5_hash.hexdigest(),
                'file_uploaded_at': (timestamp := datetime.now().isoformat()),
                'file_updated_at': timestamp
            }
        print(f'INFO - Total MD5 Hashes Calculated: {len(file_hash_details_dict)}')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S6] - {str(error)}')

    # Insert MD5 Hashes Into Database:S7
    try:
        database_connection = sqlite3.connect(str(database_file_path))
        database_cursor = database_connection.cursor()
        total_inserted = 0
        for file_path, file_hash_details in file_hash_details_dict.items():
            try:
                database_cursor.execute('''
                    INSERT INTO analysis_file_hash (file_uploaded_at, file_path, file_md5_hash, file_updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (file_hash_details['file_uploaded_at'], file_path, file_hash_details['file_hash_value'], file_hash_details['file_updated_at']))
                total_inserted += 1
            except sqlite3.IntegrityError as integrity_error:
                print(f'WARNING - [File-Delta-To-BLOB:S7] - Duplicate Entry Skipped For File: {file_path}')
        database_connection.commit()
        database_connection.close()
        print(f'INFO - Total Records Inserted Into Database: {total_inserted}')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S7] - {str(error)}')

    # Create File Hash Details JSON:S8
    try:
        with open(file_hash_details_json_path, 'w', encoding = 'utf-8') as json_file:
            json.dump(file_hash_details_dict, json_file, indent = 2)
        print(f'INFO - File Hash Details JSON Created At: {file_hash_details_json_path}')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S8] - {str(error)}')
