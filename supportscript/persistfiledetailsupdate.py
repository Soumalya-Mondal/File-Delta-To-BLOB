# Define "persist_file_details_update" Function
def persist_file_details_update(database_file_path: str, json_dump_file_path: str, added_file_hash_details_dict: dict, modified_file_hash_details_dict: dict, deleted_file_hash_details_dict: dict) -> dict[str, str]:
    # Importing Python Module:S1
    try:
        from pathlib import Path
        import sqlite3
        import json
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '1', 'message': str(error)}

    # Validate Database And JSON Dump File Paths Exist And Are Files:S2
    try:
        database_file_object = Path(database_file_path)
        json_dump_file_object = Path(json_dump_file_path)
        if not database_file_object.exists() or not database_file_object.is_file():
            raise FileNotFoundError(f'Database File Not Found Or Not A Regular File: "{database_file_path}"')
        if not json_dump_file_object.exists() or not json_dump_file_object.is_file():
            raise FileNotFoundError(f'JSON Dump File Not Found Or Not A Regular File: "{json_dump_file_path}"')
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '2', 'message': str(error)}

    # Insert Or Update Added File Details Into Database:S3
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
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '3', 'message': str(error)}

    # Insert Or Update Modified File Details Into Database:S4
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
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '4', 'message': str(error)}

    # Insert Or Update Deleted File Details Into Database:S5
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
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '5', 'message': str(error)}

    # Update JSON Dump File With Added, Modified And Deleted File Details:S6
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
        return {'status': 'ERROR', 'script_name': 'Persist-File-Details-Update', 'step': '6', 'message': str(error)}

    return {'status': 'SUCCESS', 'script_name': 'Persist-File-Details-Update', 'step': '6', 'message': 'Local File Details Persisted Successfully'}
