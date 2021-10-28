from datetime import datetime

import cassis
import time
import os

def current_milli_time():
    return round(time.time() * 1000)





def save_txt_as_xmi(txt_path:str, landtag:str, datum: str,
                    typesystem:cassis.TypeSystem, user1:str, user2:str,
                    origin_path:str, quelle:str, subtilte_protocol:str,
                    save_path:str):
    """
    landtag: parliament of the given protocol
    datum: date of the protocol with style: DD.MM.YYYY

    :param txt_path:
    :param landtag:
    :param datum:
    :param typesystem:
    :return:
    """
    with open(txt_path, "r") as f:
        text = f.read()
    cas = cassis.Cas(typesystem=typesystem)
    text = text.encode("utf-8")
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
    day = date_time_obj.strftime("%A")
    month = date_time_obj.strftime("%B")
    year = date_time_obj.year
    timestamp = datetime.timestamp(date_time_obj) * 1000
    # DocumentModification
    user1 = user1
    user2 = user2
    comment1 = "Download"
    comment2 = "Transformation/Conversion"
    timestamp2 = os.path.getmtime(origin_path) * 1000
    timestamp3 = current_milli_time()

    cas.add_all([
        DocumentMetaData(documentTitle=document_title, documentId=document_id),
        DocumentAnnotation(author=author, dateDay=day, subtitle=subtitle,
                           dateMonth=month, dateYear=year, timestamp=timestamp),
        DocumentModification(user=user1, timestamp=timestamp2, comment=comment1),
        DocumentModification(user=user2, timestamp=timestamp3, comment=comment2)
    ])

    cas.to_xmi(save_path + "/" + document_id)

    return


def main():
    with open('/home/s5935481/work4/parliament_crawler/src/convert_and_clean/TypeSystem.xml', 'rb') as f:
        typesystem = cassis.load_typesystem(f)
    mask = {
        "Reichstag": {"landtag":"Reichstag",
                      "origin_path":"/resources/corpora/parlamentary",
                      "user1":"abrami",
                      "user2":"hammerla",
                      "quelle":"BSB-Bayerische Staatsbibliothek",
                      "date_func": (lambda file_path: file_path.strip(".txt").split(" ")[-1]),
                      "subtitle": (lambda file_path: file_path.split("/")[-3].replace(" ", "") + "__" + "".join(file_path.split("/")[-1].split(" ")[0:2]))
                      }

    }

    file = "/vol/s5935481/parlamentary_reichstag_text/1867 - 1895/1. Leg.-Periode/1871,1/22. Sitzung 25.04.1871.txt"
    save_txt_as_xmi(
        file,
        mask["Reichstag"]["landtag"], mask["Reichstag"]["date_func"](file), typesystem,
        mask["Reichstag"]["user1"], mask["Reichstag"]["user2"], mask["Reichstag"]["origin_path"],
        mask["Reichstag"]["quelle"], mask["Reichstag"]["subtitle"](file),
        "/vol/s5935481/BIN")

if __name__ == "__main__":
    main()