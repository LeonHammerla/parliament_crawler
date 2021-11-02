import tqdm
from PIL import Image
import pytesseract
import sys
from pdf2image import convert_from_path
import os
from os import makedirs
import path_reader


def pdf_to_image(dir_pdf, pdf_name, output_path, dpi):
    pdf_path = f"{dir_pdf}/{pdf_name}"
    # Store all the pages of the PDF in a variable
    pages = convert_from_path(pdf_path, dpi)
    # Counter to store images of each page of PDF to image
    image_counter = 1
    makedirs(output_path, exist_ok=True)
    # Iterate through all the pages stored above
    for page in pages:
        # Declaring filename for each page of PDF as JPG
        # For each page, filename will be:
        # PDF page 1 -> page_1.jpg
        # PDF page 2 -> page_2.jpg
        # PDF page 3 -> page_3.jpg
        # ....
        # PDF page n -> page_n.jpg
        filename = "page_" + str(image_counter) + ".jpg"

        # Save the image of the page in system
        page.save(f"{output_path}/{filename}", 'JPEG')

        # Increment the counter to update filename
        image_counter = image_counter + 1
    return image_counter


def image_to_text(output_path, output_name, image_counter, lang):
    '''
    Part #2 - Recognizing text from the images using OCR
    '''
    # Variable to get count of total number of pages
    filelimit = image_counter - 1

    # Creating a text file to write the output
    outfile = f"{output_path}/text_{output_name.split('.pdf')[0]}.txt"

    # Open the file in append mode so that
    # All contents of all images are added to the same file
    f = open(outfile, "w")

    # Iterate from 1 to total number of pages
    for i in range(1, filelimit + 1):
        # Set filename to recognize text from
        # Again, these files will be:
        # page_1.jpg
        # page_2.jpg
        # ....
        # page_n.jpg
        filename = "page_" + str(i) + ".jpg"

        # Recognize the text as string in image using pytesserct
        text = str(((pytesseract.image_to_string(Image.open(f"{output_path}/{filename}"), lang=lang))))

        # The recognized text is stored in variable text
        # Any string processing may be applied on text
        # Here, basic formatting has been done:
        # In many PDFs, at line ending, if a word can't
        # be written fully, a 'hyphen' is added.
        # The rest of the word is written in the next line
        # Eg: This is a sample text this word here GeeksF-
        # orGeeks is half on first line, remaining on next.
        # To remove this, we replace every '-\n' to ''.
        text = text.replace('-\n', '')

        # Finally, write the processed text to the file.
        f.write(text)

    # Close the file after writing all the text.
    f.close()

    # Delete saved images
    for i in range(1, filelimit + 1):
        filename = "page_" + str(i) + ".jpg"
        os.remove(f"{output_path}/{filename}")


def scanned_pdf_to_text(dir_pdf, pdf_name, output_path, dpi=200, lang="eng"):
    '''
    Quelle: Angepasst von https://www.geeksforgeeks.org/python-reading-contents-of-pdf-using-ocr-optical-character-recognition/
    Overview possible languages: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
    '''
    counter = pdf_to_image(dir_pdf, pdf_name, output_path, dpi)
    image_to_text(output_path, pdf_name, counter, lang)


if __name__ == "__main__":
    # define Parameter
    data_input_dir = "/resources/corpora/parlamentary_germany/Niedersachsen/pdf"
    #output_dir = "data/output"
    end_with = ".txt"
    counter = 0
    #pdf_names = ["001.pdf", "002.pdf"]

    # get path and name for saving all_pdf_path from the input_dir
    output_name_for_path = path_reader.create_output_name_for_path(data_input_dir, end_with, 3, 5)
    print(output_name_for_path)
    # Write all path of the pdf in a .txt file
    # Run this method only one time for every different path
    path_reader.get_all_path_pdf(data_input_dir, f"{output_name_for_path[0]}/{output_name_for_path[1]}")

    # Read all path from the created .txt file and Extract the text from the pdfs in the modified output dir
    # Example for resources/corpora/parlamentary_germany/Niedersachsen/pdf/10/001.pdf will be saved in resources/corpora/parlamentary_germany/Niedersachsen/extract_text/10/001.txt
    for i in tqdm.tqdm(path_reader.read_path_pdf(f"{output_name_for_path[0]}/{output_name_for_path[1]}"), desc=f"Read text from scanned pdf files from the directory{data_input_dir}"):
        path_i, name_i = path_reader.get_path_and_name(i)
        output_i = path_reader.get_modified_output_dir(path_i, "extract_text", 5)
        # print(output_i)
        scanned_pdf_to_text(path_i, name_i, output_i, 200, lang="deu")
        # if counter >= 2:
        #      exit()
        # else:
        #     counter += 1
    # for i in path_reader.read_path_pdf(f"{output_dir}/test.txt"):
    #     print(path_reader.get_path_and_name(i))
    # for pdf_n in tqdm.tqdm(pdf_names, desc=f"Collecting text from scanned pdf: {data_input_dir}"):
    #     scanned_pdf_to_text(data_input_dir, pdf_n, output_dir, 200, lang="deu")
