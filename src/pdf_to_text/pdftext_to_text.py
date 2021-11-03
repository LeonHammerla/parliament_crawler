import pathlib
from typing import Union
import textract
from tqdm import tqdm
from PIL import Image
import pytesseract
import sys
from pdf2image import convert_from_path
import os
from multiprocessing import Pool
from functools import partial


def pdf_to_text(pdf_path:str) -> bool:
    """
    Converts pdf to txt file
    :param pdf_path:
    :return:
    """
    success = False
    try:
        text = textract.process(pdf_path)
        text = text.decode("utf-8")
        with open(pdf_path.replace("pdf", "txt"), "w") as f:
            f.write(text)
        success = True
    except:
        success = False
    return success


def dir_to_txt(dir_path:str) -> [bool]:
    """
    Converts whole pdf directory to txt
    :param dir_path:
    :return:
    """
    files = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
    successes = []
    for file in tqdm(files, desc=f"Converting {dir_path.split('/')[-1]}"):
        successes.append(pdf_to_text(file))
    return successes


def dir_of_subdirs_to_txt(dir_path:str, forbidden_dirs:Union[list, None]) -> None:
    """
    Converts a whole directory with subdirectories to txt files.
    :param dir_path:
    :param forbidden_dirs:
    :return:
    """
    dir_stack = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
    dir_stack = [file_path for file_path in dir_stack if os.path.isdir(file_path)]
    dir_with_pdf = set()
    while len(dir_stack) != 0:
        dir_path = dir_stack[0]
        sub_elems = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
        sub_files, sub_dirs = [], []
        for elem in sub_elems:
            if os.path.isdir(elem):
                sub_dirs.append(elem)
            elif os.path.isfile(elem):
                sub_files.append(elem)
            else:
                pass
        dir_stack.extend(sub_dirs)
        for sub_file in sub_files:
            if ".pdf" in sub_file:
                dir_with_pdf.add(dir_path)
        dir_stack = dir_stack[1:]
    dir_with_txt = list(dir_with_pdf)
    #print(dir_with_txt)
    if forbidden_dirs != None:
        for forbidden_dir in forbidden_dirs:
            dir_with_txt.remove(forbidden_dir)
    pool = Pool(14)
    result = pool.map(dir_to_txt, dir_with_txt)
    pool.close()
    pool.join()
    successes = []
    for sub_list in result:
        for success in sub_list:
            successes.append(success)
    good, bad = 0, 0
    for success in successes:
        if success:
            good += 1
        else:
            bad += 1
    print(f"Successes: {good}; fails: {bad}")
    return


if __name__ == "__main__":
    dir_of_subdirs_to_txt("/vol/s5935481/parlamentary/bayern/pdf", ["/vol/s5935481/parlamentary/bayern/pdf/1. Wahlperiode (1946-1950)"])