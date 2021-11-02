import os
from os import makedirs
# Help functions
list_files = []


def get_all_path_pdf(path_dir: str, dir_output: str):
    for file in os.scandir(path_dir):
        if file.is_dir():
            get_all_path_pdf(file, dir_output)
        elif (str(file.path)).endswith(".pdf"):
            list_files.append(str(file.path))
            # makedirs(os.path.dirname(dir_output), exist_ok=True)
            with open(dir_output, "a", encoding="UTF-8") as output:
                output.write(f"{str(file.path)}\n")
            if len(list_files) % 100 == 0:
                print(len(list_files))
                print(dir_output)


def read_path_pdf(path_pdfs: str):
    pdf_path_dict = set()
    with open(path_pdfs, "r", encoding="UTF-8") as file_path:
        for path_for_pdfs in file_path.readlines():
            path_for_pdfs = path_for_pdfs.replace("\n", "")
            pdf_path_dict.add(path_for_pdfs)
    return pdf_path_dict


def get_path_and_name(path_dir: str):
    splitted = path_dir.split("/")
    pdf_name = splitted[len(splitted) - 1]
    path_file = "/".join(splitted[:len(splitted) - 1])
    return path_file, pdf_name


def create_output_name_for_path(input_dir: str, end_with: str, index: int, end_index: int):
    splitted = input_dir.split("/")
    output_dir = "/".join(splitted[1:end_index])
    output_dir = f"/{output_dir}"
    output_new = "_".join(splitted[index:])
    output_new = f"{output_new}{end_with}"
    return output_dir, output_new


def get_modified_output_dir(input_dir: str, modifier: str, index: int):
    splitted = input_dir.split("/")
    pos = splitted[index]
    return input_dir.replace(f"/{pos}/", f"/{modifier}/")