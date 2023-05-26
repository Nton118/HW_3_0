from pathlib import Path
import os
from ab_classes import dir_path
import shutil
from translit import normalize
import json


CATEGORIES = {}
found_files = {}

known_types = set()
unknown_types = set()
deleted_folders = []


def read_config():
    global CATEGORIES

    with open(os.path.join(dir_path, "config.JSON")) as cfg:
        global languages
        cfg_data = json.load(cfg)
        CATEGORIES = cfg_data["FILETYPES"]
        for key in CATEGORIES:
            found_files.update({key: []})
        languages = True if cfg_data["Language"] == "eng" else False


def scan_folder(path: Path):
    contents = [x for x in path.iterdir()]
    for item in contents:
        is_unknown = True
        if item.is_file():
            ext = item.suffix[1:].upper()

            for name, types in CATEGORIES.items():
                if ext in types:
                    found_files[name].append(item)
                    known_types.add(ext)
                    is_unknown = False
                    break

            if is_unknown:
                unknown_types.add(ext)

        else:
            if item.name not in CATEGORIES.keys():
                scan_folder(item)
            else:
                continue


def move_files(files_list: list, target_path: Path, new_folder_name: str) -> list:
    output_list = []
    new_dir = target_path / new_folder_name
    try:
        new_dir.mkdir()
    except FileExistsError:
        pass
    for file in files_list:
        new_name = normalize(file.name)
        output_list.append(new_name)
        try:
            file.rename(f"{new_dir}\\{new_name}")
        except FileExistsError:
            file.unlink()  # delete doubles
    return output_list


def unpack_files(target_path: Path):
    arc_dir = target_path / "archives"
    files = [x for x in arc_dir.iterdir()]

    for file in files:
        new_name = normalize(file.name).split(".")[0]
        new_dir = arc_dir / new_name
        try:
            new_dir.mkdir()
            shutil.unpack_archive(file, new_dir)
        except (FileExistsError, shutil.ReadError):
            pass
        try:
            file.unlink()  # delete unpacked archive
        except FileNotFoundError:
            pass


def del_empty_folders(path: Path):
    folders = [x for x in path.iterdir() if x.is_dir()]
    for item in folders:
        if item.name not in CATEGORIES.keys():
            if len(list(Path(item).iterdir())) == 0:
                deleted_folders.append(item.name)
                item.rmdir()
            else:
                del_empty_folders(item)
        else:
            continue


def normalize_all(path: Path):
    items = [x for x in path.iterdir()]
    for item in items:
        if not item.is_file():
            if item.name not in CATEGORIES.keys():
                normalize_all(item)
                new_name = item.parent / normalize(item.name)
                item.rename(new_name)
            else:
                continue
        else:
            new_name = item.parent / normalize(item.name)
            item.rename(new_name)


def report_category(category: str, files_lst: list):
    if languages:
        return(f'Found files in category "{category.capitalize()}": ', len(files_lst))
    else:
        return(
            f'Знайдено файлів в категорії "{category.capitalize()}": ', len(files_lst)
        )


def sort(work_path):
    read_config()

    if not work_path:
        if languages:
            return "Please specify the target path in the parameters"
        else:
            return "Будь ласка вкажіть цільовий шлях в параметрах"

    path = Path(work_path)

    if not path.exists():
        if languages:
            return "The specified path does not exist"
        else:
            return "Вказаний шлях не існує"
    try:
        normalize_all(path)

        scan_folder(path)

        # create folders only for found file types
        for category in found_files.keys():
            if len(found_files.get(category)) > 0:
                report_category(
                    category, move_files(found_files.get(category), path, str(category))
                )

        # unpack archives if found any
        if len(found_files.get("archives")) > 0:
            unpack_files(path)

        del_empty_folders(path)

    except PermissionError:
        if languages:
            return "No change is allowed. Close the target folder or its subfolders in all other applications."
        else:
            return "Немає дозволу на зміни. Закрийте цільову теку або її підтеки в усіх інших додатках."
    if languages:
        output = f"""Found files of known types: {', '.join(f for f in known_types)}. Total {len(known_types)} files.
Found files of unknown types: {', '.join(f for f in unknown_types)}. total {len(unknown_types)} files.
Deleted empty folders {len(deleted_folders)}"""
    else:
        output = f"""Знайдено файли відомих типів: {', '.join(f for f in known_types)}. Всього {len(known_types)} файлів.
Знайдено файли невідомих типів: {', '.join(f for f in unknown_types)}. всього {len(unknown_types)} файлів.
Видалено порожніх тек {len(deleted_folders)}"""

    return output


if __name__ == "__main__":
    sort()
