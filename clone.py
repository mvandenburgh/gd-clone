from fnmatch import fnmatch
from pathlib import Path
from typing import List

import click
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile

# Constants
GDRIVE_FOLDER_TYPE: str = "application/vnd.google-apps.folder"


def download_directory(
    drive_object,
    save_to_dir: Path,
    gd_folder: str = "root",
    dirs_to_ignore: List[Path] = [],
    files_to_ignore: List[str] = [],
):
    # Create destination directory if it doesn't exist
    save_to_dir.mkdir(parents=True, exist_ok=True)

    file_list = drive_object.ListFile(
        {"q": f"'{gd_folder}' in parents and trashed=false"}
    ).GetList()

    for f in file_list:
        # A filename with ':' is valid on Google Drive, but not Unix systems
        fname: str = f["title"].replace(":", "")

        if f["mimeType"] == GDRIVE_FOLDER_TYPE:
            if fname in dirs_to_ignore:
                print(f'Ignored directory "{fname}"...')
                continue
            new_dir: Path = Path(save_to_dir) / fname
            skip = False
            for dir in dirs_to_ignore:
                for part in str(new_dir).split("/"):
                    if fnmatch(part, dir):
                        skip = True
                        print(f"Ignored directory {fname} per {dir} rule...")
                        break
                if skip:
                    break
            if skip:
                continue
            download_directory(
                drive_object,
                save_to_dir=new_dir,
                gd_folder=f["id"],
                dirs_to_ignore=dirs_to_ignore,
                files_to_ignore=files_to_ignore,
            )
        else:
            save_file_path: Path = Path(save_to_dir / fname)
            if save_file_path.is_file():  # or 'Stony Brook CSE 306 Lecture:' in fname:
                print(f"{Path(save_to_dir / fname)} already exists!")
                continue
            elif f["title"] in files_to_ignore:
                print(f"Ignored file {save_file_path}...")
                continue
            else:
                skip = False
                for file in files_to_ignore:
                    for part in str(save_file_path).split("/"):
                        if fnmatch(part, file):
                            skip = True
                            print(f"Ignored file {fname} per {file} rule...")
                            break
                    if skip:
                        break
                if skip:
                    continue
                print(f"downloading to {str(save_file_path)}")
                try:
                    f_: GoogleDriveFile = drive_object.CreateFile({"id": f["id"]})
                    f_.GetContentFile(save_file_path)
                except Exception as e:
                    print(f'\033[91m Failed to download file "{fname}" \033[0m')
                    print(str(e))


@click.command()
@click.option("--dest", help="Directory to save files to.", required=True)
@click.option("--ignore_dir", multiple=True, default=[])
@click.option("--ignore_file", multiple=True, default=[])
def clone_google_drive(dest: str, ignore_dir: List[str], ignore_file: List[str]):
    # Authentication w/ Google Drive API
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
    drive = GoogleDrive(gauth)

    return download_directory(drive, Path(dest), "root", ignore_dir, ignore_file)


if __name__ == "__main__":
    clone_google_drive()
