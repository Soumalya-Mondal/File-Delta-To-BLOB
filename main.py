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
        file_upload_folder_path = Path(parent_folder_path) / 'FileUpload'
        file_download_folder_path = Path(parent_folder_path) / 'FileDownload'
        database_folder_path = Path(parent_folder_path) / 'database'
        analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
    except Exception as error:
        print(f'ERROR - [File-Delta-To-BLOB:S2] - {str(error)}')