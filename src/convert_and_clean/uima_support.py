import pathlib
from datetime import datetime
from multiprocessing import Pool
import cassis
import time
import os
from functools import partial
from tqdm import tqdm
import re
import codecs
import traceback

# path of the corpus where all xmi files are stored
XMI_CORPUS_PATH = "/vol/s5935481/parlamentary_xmi_corpus"
# dictionary with identifiers for the different parliaments
MASK = {
        "Reichstag":    {"landtag":"Reichstag",
                        "origin_path":"/resources/corpora/parlamentary",
                        "user1":"abrami",
                        "user2":"hammerla",
                        "quelle":"BSB-Bayerische Staatsbibliothek",
                        "date_func": (lambda file_path: file_path.strip(".txt").split(" ")[-1]),
                        "subtitle": (lambda file_path: file_path.split("/")[-3].replace(" ", "") + "__" + "".join(file_path.split("/")[-1].split(" ")[0:2])),
                        "save_path": (lambda file_path: create_dirs(os.path.join(XMI_CORPUS_PATH, "reichstag", "/".join(file_path.split("/")[4:-1])))),
                        "dir_path" : "/vol/s5935481/parlamentary_reichstag_text",
                        "filter": False
                        },
        "Hamburg":      {"landtag":"Hamburgische-Bürgerschaft",
                        "origin_path":"/vol/s5935481/parlamentary/hamburg/pdf",
                        "user1":"hammerla",
                        "user2":"hammerla",
                        "quelle":"hamburgische Bürgerschaftskanzlei",
                        "date_func": (lambda file_path: date_hamburg(file_path)),
                        "subtitle": (lambda file_path: file_path.split("/")[-1].split("_")[1] + ".Wahlperiode__" + file_path.split("/")[-1].strip(".txt").split("_")[2] + ".Sitzung"),
                        "save_path": (lambda file_path: create_dirs(os.path.join(XMI_CORPUS_PATH, "hamburg", "/".join(file_path.split("/")[-2:-1])))),
                        "dir_path": "/vol/s5935481/parlamentary/hamburg/txt",
                        "filter":True
                        }

    }

def valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF or
        codepoint in (0x9, 0xA, 0xD) or
        0xE000 <= codepoint <= 0xFFFD or
        0x10000 <= codepoint <= 0x10FFFF
        )

def create_dirs(dir_path:str):
    """
    Help function to create directories, if they dont exist.
    :param dir_path:
    :return:
    """
    pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)
    return dir_path


def current_milli_time():
    """
    returns timestamp in milliseconds.
    :return:
    """
    return round(time.time() * 1000)

def date_hamburg(filepath:str):
    pattern1 = re.compile("([0-9][0-9]\\.[0-9][0-9]\\.[0-9][0-9][0-9][0-9]|[0-9][0-9]\\.[0-9][0-9]\\.[0-9][0-9])")
    pattern2 = re.compile("[0-9][0-9]\\.[0-9][0-9]\\.[0-9][0-9]")
    with open(filepath, "r") as f:
        for line in f:
            line = line.replace(" ", "")
            line = line.strip()
            z = re.match(pattern1, line)
            if z:
                zz = re.match(pattern2, line)
                if zz:
                    if int(line[-2:]) < 40:
                        line = line[:6] + "20" + line[-2:]
                    else:
                        line = line[:6] + "19" + line[-2:]
                else:
                    pass
                return line



def save_txt_as_xmi(txt_path:str, landtag:str, datum: str,
                    typesystem:cassis.TypeSystem, user1:str, user2:str,
                    origin_path:str, quelle:str, subtilte_protocol:str,
                    save_path:str, mask_key:str):
    """
    landtag: parliament of the given protocol
    datum: date of the protocol with style: DD.MM.YYYY
    Function to save a txt file as apache uima xmi.
    :param txt_path:
    :param landtag:
    :param datum:
    :param typesystem:
    :return:
    """
    with codecs.open(txt_path, "r", "utf-8") as f:
        text = f.read()
    if MASK[mask_key]["filter"]:
        text = ''.join(c for c in text if valid_xml_char_ordinal(c))
    cas = cassis.Cas(typesystem=typesystem)

    cas.sofa_string = text
    cas.sofa_mime = "text"


    DocumentMetaData = typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData")
    DocumentAnnotation = typesystem.get_type("org.texttechnologylab.annotation.DocumentAnnotation")
    DocumentModification = typesystem.get_type("org.texttechnologylab.annotation.DocumentModification")
    # DocumentMetaData
    document_title = landtag + "-Plenarprotokoll vom " + datum
    document_id = txt_path.split("/")[-1].replace(" ", "_").replace(".txt", ".xmi")
    # DocumentAnnotation
    date_time_obj = datetime.strptime(datum, '%d.%m.%Y')
    author = quelle
    subtitle = subtilte_protocol
    day = int(datum.split(".")[0])
    month = int(datum.split(".")[1])
    year = int(datum.split(".")[2])
    timestamp = int(datetime.timestamp(date_time_obj) * 1000)
    # DocumentModification
    user1 = user1
    user2 = user2
    comment1 = "Download"
    comment2 = "Transformation/Conversion"
    timestamp2 = int(os.path.getmtime(origin_path) * 1000)
    timestamp3 = int(current_milli_time())

    cas.add_all([
        DocumentMetaData(documentTitle=document_title, documentId=document_id),
        DocumentAnnotation(author=author, dateDay=day, subtitle=subtitle,
                           dateMonth=month, dateYear=year, timestamp=timestamp),
        DocumentModification(user=user1, timestamp=timestamp2, comment=comment1),
        DocumentModification(user=user2, timestamp=timestamp3, comment=comment2)
    ])

    cas.to_xmi(save_path + "/" + document_id)

    return


def save_directory_as_xmi(dir_path:str, mask_key:str, typesystem:str):
    """
    Function saves a whole directory of txt-files as xmi. it needs directory path, a typesystem for
    apache uima and a mask_key, which is ja identifier for the parliament of the given txt files.
    :param dir_path:
    :param mask_key:
    :param typesystem:
    :return:
    """
    with open('/home/s5935481/work4/parliament_crawler/src/convert_and_clean/TypeSystem.xml', 'rb') as f:
        typesystem = cassis.load_typesystem(f)
    files = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
    files = [file for file in files if os.path.isfile(file)]
    fails = []
    exceptions = set()
    for file in files:
        save_path = MASK[mask_key]["save_path"](file)

        try:
            save_txt_as_xmi(
                            txt_path=file,
                            landtag=MASK[mask_key]["landtag"],
                            datum=MASK[mask_key]["date_func"](file),
                            typesystem=typesystem,
                            user1=MASK[mask_key]["user1"],
                            user2=MASK[mask_key]["user2"],
                            origin_path=MASK[mask_key]["origin_path"],
                            quelle=MASK[mask_key]["quelle"],
                            subtilte_protocol=MASK[mask_key]["subtitle"](file),
                            save_path=save_path,
                            mask_key = mask_key
                            )
        except Exception as e:
            fails.append(file)
            exceptions.add(traceback.format_exc())
        """
        save_txt_as_xmi(
            txt_path=file,
            landtag=MASK[mask_key]["landtag"],
            datum=MASK[mask_key]["date_func"](file),
            typesystem=typesystem,
            user1=MASK[mask_key]["user1"],
            user2=MASK[mask_key]["user2"],
            origin_path=MASK[mask_key]["origin_path"],
            quelle=MASK[mask_key]["quelle"],
            subtilte_protocol=MASK[mask_key]["subtitle"](file),
            save_path=save_path,
            mask_key=mask_key
        )
        """
    return [fails, exceptions]


def parse_and_save_whole_corpus(mask_key:str, typesystem:str):
    dir_path = MASK[mask_key]["dir_path"]
    part_func = partial(save_directory_as_xmi, mask_key=mask_key, typesystem=typesystem)
    dir_stack = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
    dir_stack = [file_path for file_path in dir_stack if os.path.isdir(file_path)]
    dir_with_txt = set()
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
            if ".txt" in sub_file:
                dir_with_txt.add(dir_path)
        dir_stack = dir_stack[1:]
    dir_with_txt = list(dir_with_txt)
    pool = Pool(28)
    result = list(tqdm(pool.imap_unordered(part_func, dir_with_txt),
                       desc="Parsing and Converting to XMI; Corpus: {}".format(mask_key)))
    pool.close()
    pool.join()
    fails = []
    exceptions = []
    for fail_list in result:
        for fail in fail_list[0]:
            fails.append(fail)
        for exception in fail_list[-1]:
            exceptions.append(exception)

    for fail in list(set(fails)):
        print(fail + "\n")

    for exception in list(set(exceptions)):
        print(exception)
        print("\n")
    print(len(fails))
    return


def main():
    typesystem = '/home/s5935481/work4/parliament_crawler/src/convert_and_clean/TypeSystem.xml'
    parse_and_save_whole_corpus("Hamburg", typesystem)

if __name__ == "__main__":
    main()