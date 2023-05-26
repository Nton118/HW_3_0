import argparse 
import json
import logging
import os
import shutil
from translit import normalize
from threading import Thread, Event
from pathlib import Path
from time import sleep

CATEGORIES = {}
found_files = {}

known_types = set()
unknown_types = set()
deleted_folders = []
dir_path = os.path.dirname(__file__)


def read_config():
    global CATEGORIES

    with open(os.path.join(dir_path, "config.JSON")) as cfg:
        cfg_data = json.load(cfg)
        CATEGORIES = cfg_data["FILETYPES"]
        for key in CATEGORIES:
            found_files.update({key: []})


def th_scan_folder(path: Path, event: Event):
    scan_folder(path)
    logging.debug('Notify all')
    event.set()
    sleep(2)


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
    new_dir.mkdir(parents=True, exist_ok=True)
    for file in files_list:
        output_list.append(file.name)
        try:
            shutil.copyfile(file, new_dir / file.name)
        except OSError as err:
            logging.error(err)
    return output_list


def unpack_files(target_path: Path):
    
    arc_dir = target_path / "archives"
    arc_dir.mkdir(parents=True, exist_ok=True)
    files = [x for x in arc_dir.iterdir()]

    for file in files:
        new_dir = arc_dir / file.name
        try:
            new_dir.mkdir(exist_ok=True)
            shutil.unpack_archive(file, new_dir)
        except (FileExistsError, shutil.ReadError):
            pass
        try:
            file.unlink()  # delete unpacked archive
        except FileNotFoundError:
            pass


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
    # event.wait()
    logging.debug(f'started thread')
    return(f'Found files in category "{category.capitalize()}": ', len(files_lst))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")
    read_config()

    parser = argparse.ArgumentParser(description="Sorting folder")
    parser.add_argument("--source", "-s", help="Source folder", default="E:\\Unsorted")
    parser.add_argument("--output", "-o", help="Output folder", default="E:\\dist")
    parser.add_argument("--translit", "-t", help="Translit names", default=False)
   
    
    print(parser.parse_args())
    args = vars(parser.parse_args())
    print(args)
    transl = args.get("translit")    
    work_path = Path(args.get("source"))
    out_path = Path(args.get("output"))


    if not work_path:
        print("Please specify the target path in the parameters")
    
    if not work_path.exists():
        print("The specified path does not exist")
    
    try:
        # event = Event()
        threads = []
        # th1=Thread(target=th_scan_folder, args=(work_path, event, ))
        # th1.start()
        # threads.append(th1)
        
        scan_folder(work_path)
        # create folders only for found file types
        for category in found_files.keys():
            if len(found_files.get(category)) > 0:
                th = Thread(name={category}, target=report_category, args=(category, 
                                                          move_files(found_files.get(category),
                                                                     out_path,
                                                                     str(category)),)
                )
                th.start()
                threads.append(th)
        
        [th.join() for th in threads]
                
        # unpack archives if found any
        if len(found_files.get("archives")) > 0:
            unpack_files(out_path)
            
        if transl:
            normalize_all(out_path)

    except PermissionError:
        print("Change is not allowed. Close the target folder or its subfolders in all other applications.")

    print(f"""Found files of known types: {', '.join(f for f in known_types)}. Total {len(known_types)} files.
Found files of unknown types: {', '.join(f for f in unknown_types)}. total {len(unknown_types)} files.""")
    
    

    

    