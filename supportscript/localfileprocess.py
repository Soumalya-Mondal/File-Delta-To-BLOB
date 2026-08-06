# Define "local_file_process" Function
def local_file_process(files_delta_store_folder_path: str, analysis_engine_folder_path: str, file_path: str, job_type: str) -> dict[str, str]: #type: ignore
    # Importing Pythn Module:S1
    try:
        from pathlib import Path
        import shutil
        import hashlib
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '1', 'message': str(error)}

    # Check Folder Paths:S2
    try:
        files_delta_store_folder_object = Path(files_delta_store_folder_path)
        analysis_engine_folder_object = Path(analysis_engine_folder_path)

        if not (files_delta_store_folder_object.exists() and files_delta_store_folder_object.is_dir()):
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '2', 'message': f'Files Delta Store Folder Path Does Not Exist Or Is Not A Directory: "{files_delta_store_folder_object.name}"'}

        if not (analysis_engine_folder_object.exists() and analysis_engine_folder_object.is_dir()):
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '2', 'message': f'Analysis Engine Folder Path Does Not Exist Or Is Not A Directory: "{analysis_engine_folder_object.name}"'}
    except Exception as error:
        return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '2', 'message': str(error)}

    # If Job Type Is ADD
    if str(job_type).strip().lower() == 'add':
        # Check If New Added File Already Present Or Not And File Present In Files Delta Store:S3
        try:
            add_analysis_engine_full_file_path_object = analysis_engine_folder_object / file_path
            if add_analysis_engine_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '3', 'message': f'File Already Present: "{add_analysis_engine_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Not Present In Analysis Engine: "{add_analysis_engine_full_file_path_object.name}"')

            add_files_delta_store_full_file_path_object = files_delta_store_folder_object / file_path
            if not add_files_delta_store_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '3', 'message': f'File Not Present In Files Delta Store: "{add_files_delta_store_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Present In Files Delta Store: "{add_files_delta_store_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '3', 'message': str(error)}

        # File Copy From Files Delta Store To Analysis Engine:S4
        try:
            add_analysis_engine_full_file_path_object.parent.mkdir(parents = True, exist_ok = True)
            shutil.copy2(add_files_delta_store_full_file_path_object, add_analysis_engine_full_file_path_object)
            print(f'{"[INFO]":<10} File Copied To Analysis Engine: "{add_analysis_engine_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '4', 'message': str(error)}

        # Verify File Size And MD5 Hash After Copy:S5
        try:
            add_source_file_size = add_files_delta_store_full_file_path_object.stat().st_size
            add_target_file_size = add_analysis_engine_full_file_path_object.stat().st_size

            add_source_md5_hash = hashlib.md5()
            with open(add_files_delta_store_full_file_path_object, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    add_source_md5_hash.update(chunk)

            add_target_md5_hash = hashlib.md5()
            with open(add_analysis_engine_full_file_path_object, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    add_target_md5_hash.update(chunk)

            if (add_source_file_size != add_target_file_size) and (add_source_md5_hash.hexdigest() != add_target_md5_hash.hexdigest()):
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '5', 'message': f'File Size And MD5 Hash Mismatch: Size Source="{add_source_file_size}" Target="{add_target_file_size}" MD5 Source="{add_source_md5_hash.hexdigest()}" Target="{add_target_md5_hash.hexdigest()}"'}

            return {'status': 'SUCCESS', 'script_name': 'Local-File-Process', 'step': '5', 'message': f'File Verified Successfully: Size="{add_target_file_size}" MD5="{add_target_md5_hash.hexdigest()}"'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '5', 'message': str(error)}

    # If Job Type Is MODIFIED
    if str(job_type).strip().lower() == 'modified':
        # Check If File Present In Analysis Engine And Files Delta Store:S6
        try:
            modified_analysis_engine_full_file_path_object = analysis_engine_folder_object / file_path
            if not modified_analysis_engine_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '6', 'message': f'File Not Present In Analysis Engine: "{modified_analysis_engine_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Present In Analysis Engine: "{modified_analysis_engine_full_file_path_object.name}"')

            modified_files_delta_store_full_file_path_object = files_delta_store_folder_object / file_path
            if not modified_files_delta_store_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '6', 'message': f'File Not Present In Files Delta Store: "{modified_files_delta_store_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Present In Files Delta Store: "{modified_files_delta_store_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '6', 'message': str(error)}

        # Delete Old File From Analysis Engine:S7
        try:
            modified_analysis_engine_full_file_path_object.unlink()
            if modified_analysis_engine_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '7', 'message': f'File Not Deleted From Analysis Engine: "{modified_analysis_engine_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Deleted From Analysis Engine: "{modified_analysis_engine_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '7', 'message': str(error)}

        # File Copy From Files Delta Store To Analysis Engine:S8
        try:
            modified_analysis_engine_full_file_path_object.parent.mkdir(parents = True, exist_ok = True)
            shutil.copy2(modified_files_delta_store_full_file_path_object, modified_analysis_engine_full_file_path_object)
            print(f'{"[INFO]":<10} File Copied To Analysis Engine: "{modified_analysis_engine_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '8', 'message': str(error)}

        # Verify File Size And MD5 Hash After Copy:S9
        try:
            source_file_size = modified_files_delta_store_full_file_path_object.stat().st_size
            target_file_size = modified_analysis_engine_full_file_path_object.stat().st_size

            source_md5_hash = hashlib.md5()
            with open(modified_files_delta_store_full_file_path_object, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    source_md5_hash.update(chunk)

            target_md5_hash = hashlib.md5()
            with open(modified_analysis_engine_full_file_path_object, 'rb') as file:
                while chunk := file.read(4 * 1024 * 1024):
                    target_md5_hash.update(chunk)

            if (source_file_size != target_file_size) and (source_md5_hash.hexdigest() != target_md5_hash.hexdigest()):
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '9', 'message': f'File Size And MD5 Hash Mismatch: Size Source="{source_file_size}" Target="{target_file_size}" MD5 Source="{source_md5_hash.hexdigest()}" Target="{target_md5_hash.hexdigest()}"'}

            return {'status': 'SUCCESS', 'script_name': 'Local-File-Process', 'step': '9', 'message': f'File Verified Successfully: Size="{target_file_size}" MD5="{target_md5_hash.hexdigest()}"'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '9', 'message': str(error)}

    # If Job Type Is DELETE
    if str(job_type).strip().lower() == 'delete':
        # Check If File Present In Analysis Engine:S10
        try:
            delete_analysis_engine_full_file_path_object = analysis_engine_folder_object / file_path
            if not delete_analysis_engine_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '10', 'message': f'File Not Present In Analysis Engine: "{delete_analysis_engine_full_file_path_object.name}"'}
            print(f'{"[INFO]":<10} File Present In Analysis Engine: "{delete_analysis_engine_full_file_path_object.name}"')
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '10', 'message': str(error)}

        # Delete File From Analysis Engine:S11
        try:
            delete_analysis_engine_full_file_path_object.unlink()
            if delete_analysis_engine_full_file_path_object.exists():
                return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '11', 'message': f'File Not Deleted From Analysis Engine: "{delete_analysis_engine_full_file_path_object.name}"'}
            return {'status': 'SUCCESS', 'script_name': 'Local-File-Process', 'step': '11', 'message': f'File Deleted From Analysis Engine: "{delete_analysis_engine_full_file_path_object.name}"'}
        except Exception as error:
            return {'status': 'ERROR', 'script_name': 'Local-File-Process', 'step': '11', 'message': str(error)}