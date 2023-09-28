from robocorp import browser
from robocorp.tasks import task

# from RPA.Excel.Files import Files as Excel
from RPA.HTTP import HTTP

from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

import base64

robot_site = "https://robotsparebinindustries.com"
img_format = "png"
path_files = "./output/receipts/"

browser.configure(
    browser_engine="chromium",
    screenshot="only-on-failure",
    headless=False, #False debug
    slowmo=100,
)

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    ordini = get_orders()
    # print(ordini)
    open_robot_order_website(ordini)
    
    return


def open_robot_order_website(ordini):
    """
    - apre sito
    - chiude pubblicita
    """

    page = browser.goto("https://robotsparebinindustries.com/#/robot-order")
    page.set_default_timeout(0)

    # chiude spam
    close_annoying_modal()

    # esegue per ogni ordine la richiesta
    for row in ordini:
        # print(row)
        fill_the_form(row)

        # prepara pagina per nuovo ordine
        page.click("#order-another")
        close_annoying_modal()

    archive_receipts()

    return


def fill_the_form(row):
    """
    Use the order row that you got from the loop you built as the argument for this form filler function.
    If the name of the variable you got from the loop is, for example, row, you can access the value of the Order number column like this: row['Order number'].
    You need functions for selecting things and inputting text. You have a library you need already imported!
    The input element for the leg number is slightly annoying. It does have an id attribute, but the value seems to change all the time! 🤬 Can you think of a way of targeting that element? There are no "correct" answers here, just many options!
    """

    page = browser.page()

    OrderVal = str(row['Order number'])
    print("[i] ordine: " + OrderVal)
    ## document.querySelector('#head > option:nth-child(2)'); => value="1"
    HeadVal_dom = str(int(row['Head']) + 1) # +1 per rif child nel dom
    HeadVal = str(row['Head'])
    BodyVal = row['Body']
    LegsVal = str(row['Legs'])
    AddressVal = str(row['Address'])

    # Head | area
    """
    /html/body/form/select/option
    /html/body/form/select/option[1]
    /html/body/form/select/option[position() = 1]
    /html/body/form/select/option[@value='first option']

    ## TEST CODE
    
    function getElementByXpath(path) {
        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    }

    getElementByXpath("/html/body/div/div/div[1]/div/div[1]/form/div[1]/select/option[2]") # OK
    getElementByXpath("//select[@id='head']/option[2]") # OK
    """
    try:
        head_xpath = '#head'
        page.select_option(head_xpath, HeadVal)
    except:
        print("An exception occurred")

    # Body | area
    page.click('#id-body-' + BodyVal)

    # Legs | area
    xpath_input_part_number = ".form-group:nth-child(3) > input" # va preso cosi perche id dinamico
    page.fill(xpath_input_part_number, LegsVal)
    page.fill("#address", AddressVal)

    page.click("#preview")

    # esegue altre funzioni
    screenshot_robot(OrderVal)
    store_receipt_as_pdf(OrderVal)

    return


def store_receipt_as_pdf(order_number):
    """
    You need to import an RPA Framework library that handles PDF files.
    The function needs to take an argument (the order number - to be used in the file name to ensure a unique name) and return a result (the file system path to the PDF file).
    The Beginners' python course contains a chapter about this exact topic.
    You want to store the PDF files inside the output directory (you can use subdirectories such as receipts inside the output dir if you like), since that location is supported by Control Room when it stores the process output artifacts. If you place stuff elsewhere, it will not end up in Control Room process output artifacts.
    """
    pdf_file = path_files + "robot-" + order_number + ".pdf"
    screenshot = path_files + "img-" + order_number + "." + img_format

    # crea PDF partendo pagina web
    page = browser.page()

    # show model info
    # page.click('.form-group:nth-child(1) > button')
    # robot_html = page.locator("#model-info").inner_html()

    # conferma ordine!
    problemiPagina = True
    while problemiPagina:
        try:
            page.click("#order")
        except:
            page.click("#order")

        # gestione errori pagina web
        # <div class="alert alert-danger" role="alert">Request Got Lost Error</div>
        # <div class="alert alert-danger" role="alert">Submit Button Stuck Error</div>
        # <div class="alert alert-danger" role="alert">Guess what? A server Error!</div>
        if page.is_visible(".alert-danger") == True:
            print("[>] riconferma ordine " + str(order_number))
            
            try:
                print("[!] errore pagina web: " + page.text_content(".alert-danger"))
            except:
                print("[!] text errore non trovato")
        else:
            problemiPagina = False

    # prende html dall ordine eseguito
    robot_html = page.locator("#receipt").inner_html()

    # https://robocorp.com/docs/courses/beginners-course-python/creating-pdf
    pdf = PDF()
    pdf.html_to_pdf(robot_html, pdf_file)

    # appende foto al pdf dallo screenshot
    embed_screenshot_to_receipt(screenshot, pdf_file)

    return


def screenshot_robot(order_number):
    """
    This is similar to the last function you implemented (takes an argument, returns a result).
    You have a library you need already imported.
    """

    page = browser.page()

    element = page.locator("#robot-preview-image")

    base64_photo = browser.screenshot(element, image_type=img_format)

    # import cv2
    # import numpy as np
    # jpg_original = base64.b64decode(base64_photo)
    # jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    # img = cv2.imdecode(jpg_as_np, flags=1)

    # https://www.codespeedy.com/convert-base64-string-to-image-in-python/
    # import pybase64
    # decoded_data=pybase64.b64decode((base64_photo))

    # converte base64 => string
    # https://stackoverflow.com/questions/13262125/how-to-convert-from-base64-to-string-python-3-2
    # https://medium.com/bugs-that-bite/unicodedecodeerror-utf-8-codec-can-t-decode-byte-0x89-in-position-1-invalid-start-byte-25e9f8dd3038
    # base64_string = base64.b64decode(base64_photo.decode())
    # base64_string = base64.b64decode(base64_bytes)
    # screenshot = '<img src="data:image/png;base64,' + base64_string + '"/>'

    # save image to disk
    imageName = path_files + 'img-' + str(order_number) + '.' + img_format
    decodeit = open(imageName, 'wb')
    base64_bytes = base64.b64encode(base64_photo)
    decodeit.write(base64.b64decode(base64_bytes))
    decodeit.close()

    # TODO: usare Take_Screenshot con altra lib

    return


def embed_screenshot_to_receipt(screenshot, pdf_file):
    """
    You have the library you need already imported.
    The function that adds your screenshot to the PDF also takes care of opening and closing the PDF document. How convenient!
    You want to append the screenshot to the end of the document, not replace it entirely.
    """ 

    # appende foto al pdf dallo screenshot
    # https://robocorp.com/docs/libraries/rpa-framework/rpa-pdf/keywords#add-files-to-pdf
    pdf = PDF()
    
    # merge file originale + foto robot
    list_of_files = [
        pdf_file,
        screenshot + ':align=center',
    ]
    pdf.add_files_to_pdf(
        files=list_of_files,
        target_document=pdf_file
    )

    return


def archive_receipts():
    """
    You need an RPA Framework library that can create ZIP archives. You will, of course, use the Python flavour.
    Sometimes you need to look deeper than the Readme
    """

    lib = Archive()
    lib.archive_folder_with_zip(path_files, './output/robots.zip')

    return


def close_annoying_modal():
    """
    You have already imported the library you need.
    Functions that click on things might prove useful here.
    The "click on stuff" function needs a locator so that they know what to click on. Locators are the bread and butter of automating web applications. It is good to spend some time reading about those.
    You can use the browser inspector tools to find the elements to click on.
    You can target HTML elements either with CSS type, class, ID, or attribute selectors or XPath expressions, or a combination of CSS, XPath, and text selectors.
    """

    page = browser.page()
    
    """
    <div class="alert-buttons">
        <button type="button" class="btn btn-dark">OK</button>

    ## test
    document.querySelector('.alert-buttons > button:nth-child(1)');
    """
    # xpath = "/html/body/div/div/div[2]/div/div/div/div/div/button[1]"
    xpath = '.alert-buttons > button:nth-child(1)'
    #page.click("input:text('Submit')")
    page.click(xpath)

    return


def get_orders():
    """
    - download csv
    - return data as Table
    """

    fileCsv = 'output/orders.csv'
    
    # abilitare overwrite
    HTTP().download("https://robotsparebinindustries.com/orders.csv", fileCsv, overwrite=True)

    library = Tables()
    return library.read_table_from_csv(fileCsv)

    FiltroColonne = ["Order number" , "Head", "Body", "Legs", "Address"]

    # i dati sono formattati cosi => {'Order number': '', 'Head': '' ... }
    dataset = library.read_table_from_csv(
        fileCsv, columns=FiltroColonne, encoding='utf-8'
    )
    #print (downloadedUsers)
    return dataset

    # i dati sono formattati cosi => [Table(columns=['Nome', 'Cognome'], rows=1)
    datasetList = library.group_table_by_column(dataset, "Nome visualizzato")