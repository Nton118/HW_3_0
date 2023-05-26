"""
Відсортувати файли в папці.
"""

import argparse
from pathlib import Path
from shutil import copyfile
from threading import Thread, Condition
import logging

"""
--source [-s] 
--output [-o] default folder = dist
"""

parser = argparse.ArgumentParser(description="Sorting folder")
parser.add_argument("--source", "-s", help="Source folder", required=True)
parser.add_argument("--output", "-o", help="Output folder", default="dist")

print(parser.parse_args())
args = vars(parser.parse_args())
print(args)

source = Path(args.get("source"))
output = Path(args.get("output"))

folders = []


def grabs_folder(path: Path, cond: Condition) -> None:
    
    for el in path.iterdir():
        if el.is_dir():
            folders.append(el)
            grabs_folder(el)
    with cond:
        cond.notify_all()

def copy_file(path: Path, cond: Condition) -> None:
    with cond:
        cond.wait()
    for el in path.iterdir():
        if el.is_file():
            ext = el.suffix[1:]
            new_folder = output / ext
            try:
                new_folder.mkdir(parents=True, exist_ok=True)
                copyfile(el, new_folder / el.name)
            except OSError as err:
                logging.error(err)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(threadName)s %(message)s")
    cond = Condition()
    print(source, output)
    folders.append(source)
    threads = []
    th1 = Thread(target=copy_file, args=(grabs_folder(source, cond,)))
    th1.start()
    threads.append(th1)
    
    print(folders)

    
    for folder in folders:
        th = Thread(target=copy_file, args=(folder, cond,))
        th.start()
        threads.append(th)

    [th.join() for th in threads]

    print("Можно видалити стару папку якщо треба")