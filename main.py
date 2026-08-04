# Define Main Function
if __name__ == '__main__':
    # Importing Python Module:S1
    try:
        import sys
        from pathlib import Path
    except Exception as error:
        print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S1] - {str(error)}')

    # Appending System Path:S2
    try:
        sys.path.append(str(Path.cwd()))
    except Exception as error:
        print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S2] - {str(error)}')

    # Importing User Define Function:S3
    try:
        from supportscript.rebasefilesdetails import rebase_files_details
        from supportscript.refreshcodebase import refresh_code_base
    except Exception as error:
        print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S3] - {str(error)}')

    # Define Folder Path:S4
    try:
        parent_folder_path = Path.cwd()
        env_file_path = Path(parent_folder_path) / '.env'
        database_folder_path = Path(parent_folder_path) / 'database'
        database_folder_path.mkdir(parents = True, exist_ok = True)
        files_delta_store_folder_path = Path(parent_folder_path) / 'FilesDeltaStore'
        files_delta_store_folder_path.mkdir(parents = True, exist_ok = True)
        database_file_path = Path(database_folder_path) / 'AnalysisFileHash.db'
        file_hash_details_json_path = Path(parent_folder_path) / 'FileHashDetails.json'
        analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
    except Exception as error:
        print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S4] - {str(error)}')

    # Calling Operation Menu:S5
    try:
        print('~' * 50)
        print('[A] -> Rebase Files Details')
        print('[B] -> Refresh Code Base')
        print('~' * 50)
        user_choice = input('Please Enter Your Choice: ').strip().upper()
    except Exception as error:
        print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S5] - {str(error)}')

    # If User Choose Option-A As File Rebase:S6
    if user_choice == 'A':
        try:
            print('')
            print('~' * 25, ' Rebase Files Details ', '~' * 25)
            rebase_result = rebase_files_details(env_file_path = str(env_file_path), database_file_path = str(database_file_path), json_dump_file_path = str(file_hash_details_json_path), analysis_engine_folder_path = str(analysis_engine_folder_path))
            print(f'{"[" + str(rebase_result.get("status")) + "]":<10} {str(rebase_result.get("message"))}')
            print('~' * 84)
        except Exception as error:
            print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S6] - {str(error)}')

    # If User Choose Option-B As Refresh Code Base:S7
    elif user_choice == 'B':
        try:
            print('')
            print('~' * 25, ' Refresh Code Base ', '~' * 25)
            refresh_code_base_result = refresh_code_base(env_file_path = str(env_file_path), database_file_path = str(database_file_path), json_dump_file_path = str(file_hash_details_json_path), analysis_engine_folder_path = str(analysis_engine_folder_path), files_delta_store_folder_path = str(files_delta_store_folder_path))
            print(f'{"[" + str(refresh_code_base_result.get("status")) + "]":<10} {str(refresh_code_base_result.get("message"))}')
            print('~' * 84)
        except Exception as error:
            print(f'{"[ERROR]":<10} [File-Delta-To-BLOB:S7] - {str(error)}')

    # If User Choose Invalid Option:S9
    else:
        print(f'{"[WARNING]":<10} [File-Delta-To-BLOB:S9] - Invalid Choice. Please enter A or B.')
