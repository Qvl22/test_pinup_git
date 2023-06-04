import time
import itertools 
import subprocess
from pathlib import Path
from typing import List


FOLDERS_TO_CHECK = [Path('payments'), Path('bets')]
SCRIPT2_PATH = Path('script2.py')


def watch_folders() -> None:
    """
    Monitors the specified folders for changes and executes script2.py if changes are detected.
    """
    previous_state: List[str] = get_files(FOLDERS_TO_CHECK)
    while True:
        time.sleep(1)
        current_state: List[str] = get_files(FOLDERS_TO_CHECK)

        if current_state != previous_state:
            print("Folder state has changed.")
            subprocess.run(["python", "script2.py"])
        previous_state = current_state
        
        
def get_files(folders: List[Path]) -> List[str]:
    """
    Retrieves the list of folders.
    Args:
        folders: A list of folders to check.
    Returns:
        A list of filenames present in the specified folders.
    """
    folder_files = []

    for gen in itertools.chain(map(lambda x: x.glob('*.csv'), folders)):
        for file in gen:    
            folder_files.append(file.name)

    return folder_files
    

if __name__ == "__main__":
    watch_folders()
