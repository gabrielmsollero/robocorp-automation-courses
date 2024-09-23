import os

from robocorp import browser
from robocorp.tasks import task

from RPA.Tables import Tables
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive

tmp_folder_filename = "tmp"


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    os.makedirs(tmp_folder_filename, exist_ok=True)
    browser.configure(
        slowmo=10,
    )
    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        submit_untill_success()

        order_number = order["Order number"]
        pdf_filename = store_receipt_as_pdf(order_number)
        screenshot_filename = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot_filename, pdf_filename)
        click_order_another()

    archive_receipts()


def open_robot_order_website():
    """Navigates to robot order URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def close_annoying_modal():
    """Closes annoying modal that pops up on order page opening"""
    page = browser.page()
    page.click("button:text('I guess so...')")


def get_orders():
    """Downloads CSV file and fetches orders from it"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    tables = Tables()
    return tables.read_table_from_csv("orders.csv")


def fill_the_form(order):
    """Fills the order form using one entry from the CSV file"""
    page = browser.page()
    page.select_option("#head", order["Head"])
    page.check(f"#id-body-{order['Body']}")
    page.fill('input[placeholder="Enter the part number for the legs"]', order["Legs"])
    page.fill("#address", order["Address"])


def submit_untill_success():
    """Clicks 'Order' button until there are no errors"""
    page = browser.page()
    page.click("#order")
    while page.query_selector("div.alert-danger"):
        page.click("#order")


def store_receipt_as_pdf(order_number: str) -> str:
    """Saves the order receipt as PDF and returns its filename"""
    filename = f"tmp/receipts/receipt-{order_number}.pdf"
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, filename)
    return filename


def screenshot_robot(order_number: str) -> str:
    """Takes a screenshot of the ordered robot and returns the screenshot
    filename"""
    filename = f"tmp/screenshots/screenshot-{order_number}.png"
    page = browser.page()
    page.query_selector("#robot-preview-image").screenshot(path=filename)
    return filename


def embed_screenshot_to_receipt(screenshot_filename, pdf_filename):
    """Given the filenames of a receipt and a screenshot, append the screenshot
    to the end of the receipt and save the result to a new PDF"""
    pdf = PDF()
    pdf.add_files_to_pdf(
        target_document=pdf_filename, files=[screenshot_filename], append=True
    )


def click_order_another():
    """Moves back from order completion page to new order page"""
    page = browser.page()
    page.click("#order-another")


def archive_receipts():
    """Compresses the receipts folder to a zip file"""
    archive = Archive()
    archive.archive_folder_with_zip("tmp/receipts", "output/receipts.zip")
