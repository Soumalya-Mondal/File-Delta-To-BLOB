# Define Main Function
if __name__ == '__main__':
    # Importing Python Module:S1
    try:
        from pathlib import Path
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S1] - {str(error)}')

    # Define Folder Path:S2
    try:
        parent_folder_path = Path.cwd()
        env_file_path = Path(parent_folder_path) / '.env'
        database_folder_path = Path(parent_folder_path) / 'database'
        database_folder_path.mkdir(parents = True, exist_ok = True)
        database_file_path = Path(database_folder_path) / 'AnalysisFileHash.db'
        file_hash_details_json_path = Path(parent_folder_path) / 'FileHashDetails.json'
        analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S2] - {str(error)}')

