import time
import logging
import argparse
import signal
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# -------------------------------
# Debug Mode - Set to True when troubleshooting
# -------------------------------
DEBUG = False  # Set to True only when detailed debugging is needed

# -------------------------------
# Parse Command Line Arguments
# -------------------------------
parser = argparse.ArgumentParser(description='Download Kindle books from Amazon library')
parser.add_argument('--start', type=int, default=1, help='Starting page number (default: 1)')
parser.add_argument('--end', type=int, help='Ending page number (default: all pages)')
args = parser.parse_args()

# Flag for handling keyboard interrupt
running = True

# -------------------------------
# Print ASCII Art Logo and Instructions
# -------------------------------
ascii_logo = r"""
 ____        __                                            
|  _ \  ___ / _|_ __ __ _  __ _  __ _   ___ ___  _ __ ___  
| | | |/ _ \ |_| '__/ _` |/ _` |/ _` | / __/ _ \| '_ ` _ \ 
| |_| |  __/  _| | | (_| | (_| | (_| || (_| (_) | | | | | |
|____/ \___|_| |_|  \__,_|\__, |\__, (_)___\___/|_| |_| |_|
                          |___/ |___/                      
"""

print(ascii_logo)
print("\nDefragg.com Kindle Bulk Downloader")
print("\nDefragg is a weekly newsletter that provides curated tech tutorials, productivity tips, life hacks, retro games, nostalgia, and a dash of humor delivered to your inbox.")
print("\nWe developed this script for our personal use, but decided to share it with the wider community. If you like it, you can say thanks by checking out our website or signing up for our newsletter where we share lots of other cool tech-related tips and tricks.")
print("\n========== INSTRUCTIONS ==========")
print("1. After pressing Enter, a Chrome window will launch. Please log in to your Amazon account on that page.")
print("2. A few seconds after logging in, a device selection dialog will appear above the Chrome window. Choose a Kindle device to use.")
print("3. The script will start downloading books. Activity output will be shown here in the console and logged to a file.")
print("4. You can open or interact with other windows while the script is running. The Chrome window does not have to stay focused. However, DO NOT minimize or interact with the Chrome window while the script is running!")
print("===================================\n")

# Wait for user to press a key
input("Press Enter to continue...")

# -------------------------------
# Setup Logging: File and Console Handlers
# -------------------------------
log_filename = f"kindle-download-log-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logger = logging.getLogger("KindleDownloader")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Set debug level if DEBUG is True
if DEBUG:
    logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

# -------------------------------
# Track Book Statistics
# -------------------------------
successful_downloads = 0
skipped_books = []
book_stats = {
    "total_processed": 0,
    "total_successful": 0,
    "unavailable": 0,
    "library_loans": 0,
    "errors": 0
}

# -------------------------------
# Helper Functions for Finding Elements
# -------------------------------
def find_and_click_download_option(driver):
    """
    Find and click the Download & transfer via USB option using multiple methods.
    
    Args:
        driver: WebDriver instance
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Method 1: Find all visible dropdown menu items and check each one's text
        menu_items = driver.find_elements(By.XPATH, 
            "//div[contains(@style, 'cursor: pointer') and contains(@style, 'border-bottom')]//div[contains(@style, 'padding-top') and contains(@style, 'padding-bottom')]")
        
        if DEBUG:
            logger.debug(f"Found {len(menu_items)} menu items")
        
        for item in menu_items:
            item_text = item.text.strip()
            # Only log non-empty text items to reduce noise
            if DEBUG and item_text:
                logger.debug(f"Menu item text: '{item_text}'")
            
            if "Download & transfer via USB" in item_text:
                logger.debug(f"Found menu item with text: {item_text}")
                driver.execute_script("arguments[0].click();", item)
                return True
        
        # Method 2: Use a more direct XPath to target the specific structure
        xpath = "//div[contains(@style, 'border-bottom')]//div[.//span[contains(text(), 'Download') and contains(text(), 'USB')]]"
        download_items = driver.find_elements(By.XPATH, xpath)
        
        if download_items:
            logger.debug(f"Found {len(download_items)} download items by XPath")
            driver.execute_script("arguments[0].click();", download_items[0])
            return True
            
        # Method 3: Try to find by span text directly
        span_xpath = "//span[contains(text(), 'Download') and contains(text(), 'transfer') and contains(text(), 'USB')]"
        span_elements = driver.find_elements(By.XPATH, span_xpath)
        
        if span_elements:
            logger.debug(f"Found {len(span_elements)} span elements with Download & transfer text")
            # Click the parent div of the span
            parent = span_elements[0].find_element(By.XPATH, "./..")
            driver.execute_script("arguments[0].click();", parent)
            return True
            
        logger.error("Could not find Download & transfer option using any method")
        
        # Debug all visible spans to see what options are available, but only when in DEBUG mode
        if DEBUG:
            all_spans = driver.find_elements(By.XPATH, "//div[contains(@style, 'visibility: visible')]//span")
            logger.debug(f"All visible spans ({len(all_spans)}):")
            # Only log spans with actual text to reduce noise
            for span in all_spans:
                if span.text.strip():
                    logger.debug(f"  - '{span.text}'")
            
        return False
    except Exception as e:
        logger.error(f"Error finding/clicking download option: {e}")
        return False

def find_confirm_button(driver, book_id):
    """
    Find the confirm download button in the active dialog.
    
    Args:
        driver: WebDriver instance
        book_id: ID of the current book to help scope the search
        
    Returns:
        The button element or raises an exception if not found
    """
    # Find the active dialog first (the one that's visible)
    try:
        dialog = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, 
                "//div[contains(@class, 'DeviceDialogBox-module_container') and not(contains(@class, 'hidden'))]"))
        )
        
        # Now find the confirm button within this dialog
        button = WebDriverWait(dialog, 10).until(
            EC.element_to_be_clickable((By.XPATH, 
                ".//div[contains(@class, 'DeviceDialogBox-module_button_container')]//div[.//span[text()='Download']]"))
        )
        return button
    except TimeoutException:
        # Fallback: try to find any visible dialog with an enabled button
        logger.warning(f"Could not find standard download button for book ID {book_id}. Trying alternative approach.")
        dialog = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, 
                "//div[contains(@class, 'DeviceDialogBox-module_container') and not(contains(@class, 'hidden'))]"))
        )
        
        # Find the non-disabled button (the one without opacity: 0.5)
        buttons = dialog.find_elements(By.XPATH, ".//div[contains(@class, 'DeviceDialogBox-module_button_container')]//div[contains(@style, 'background')]")
        for button in buttons:
            style = button.get_attribute("style")
            if "opacity: 0.5" not in style:
                return button
        
        raise TimeoutException("Could not find enabled download button in dialog")

# Function to print summary and exit
def print_summary_and_exit(driver=None):
    import os  # Add this at the top of the file with other imports
    
    logger.info("\n\n=== DOWNLOAD SUMMARY ===")
    logger.info(f"Total books processed: {book_stats['total_processed']}")
    logger.info(f"Successfully downloaded: {book_stats['total_successful']}")
    logger.info(f"Skipped - Library loans: {book_stats['library_loans']}")
    logger.info(f"Skipped - Unavailable: {book_stats['unavailable']}")
    logger.info(f"Skipped - Errors: {book_stats['errors']}")

    # Write skipped books to a separate log file
    if skipped_books:
        skipped_log_filename = f"skipped-books-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(skipped_log_filename, "w", encoding="utf-8") as f:
            f.write("=== SKIPPED BOOKS ===\n\n")
            for book in skipped_books:
                f.write(f"Title: {book['title']}\n")
                f.write(f"Book ID: {book['id']}\n")
                f.write(f"Page: {book['page']}, Book: {book['position']}\n")
                f.write(f"Reason: {book['reason']}\n")
                f.write("---\n")
        logger.info(f"List of skipped books saved to {skipped_log_filename}")

    logger.info("✅ All downloads initiated! Check your browser's downloads folder.")
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    input("\nPress Enter to exit...")
    os._exit(0)  # Force immediate exit

# Signal handler for Ctrl+C
def signal_handler(sig, frame):
    global running
    if not running:  # If already stopping, ignore additional Ctrl+C
        return
    print("\n\nCtrl+C detected. Finishing up and showing summary...")
    running = False
    try:
        print_summary_and_exit(driver)
    except Exception as e:
        # If something goes wrong during cleanup, still try to show summary
        print("\nError during cleanup:", str(e))
        print_summary_and_exit(None)

signal.signal(signal.SIGINT, signal_handler)

# -------------------------------
# Get starting page from command line args
# -------------------------------
start_page = args.start
logger.info(f"Starting from page {start_page}")

# -------------------------------
# Setup Chrome WebDriver with custom window size/position
# -------------------------------
options = webdriver.ChromeOptions()
prefs = {
    "download.prompt_for_download": False,
    "profile.default_content_setting_values.automatic_downloads": 1
}
options.add_experimental_option("prefs", prefs)
# Set window size to 1200x900
options.add_argument("window-size=1200,900")
options.add_argument("window-position=100,100")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# -------------------------------
# Open Kindle Content Page and Wait for Login
# -------------------------------
driver.get("https://www.amazon.com/hz/mycd/digital-console/contentlist/booksAll")
logger.info("Waiting for login... (log in on the Chrome window; do not minimize it)")
# Wait up to 5 minutes for the pagination div (indicating that login is complete)
WebDriverWait(driver, 300).until(
    EC.presence_of_element_located((By.ID, "pagination"))
)
logger.info("Login detected, continuing...")
time.sleep(3)

# -------------------------------
# Extract Device List via a Temporary Download Dialog
# -------------------------------
logger.info("\n=== Extracting device list ===")
devices = []
found_device_list = False

# Get all "More actions" buttons on the first page
more_actions_buttons = driver.find_elements(By.XPATH, "//div[contains(@id, 'MORE_ACTION')]")
for button in more_actions_buttons:
    try:
        # Get the parent row and check if the book is available for download
        book_row = button.find_element(By.XPATH, "./ancestor::tr")
        unavailable = book_row.find_elements(
            By.XPATH, 
            ".//div[contains(@class, 'information_row')]/span[contains(text(), 'This title is unavailable for download and transfer')]"
        )
        if unavailable:
            continue

        # Scroll and click the More actions button to reveal options
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(0.5)

        # Extract book ID from the title element (needed for dialog identification)
        title_element = book_row.find_element(By.XPATH, ".//div[contains(@class, 'digital_entity_title')]")
        book_id = title_element.get_attribute("id").split("-")[-1]
        
        # Click the "Download & Transfer via USB" button - UPDATED
        if not find_and_click_download_option(driver):
            logger.error("Failed to click Download & transfer option during device extraction. Trying next book.")
            continue
        time.sleep(1)

        # Wait for the device list to appear and extract device names
        device_list_xpath = f"//ul[@id='download_and_transfer_list_{book_id}']//div[contains(@class, 'ActionList-module_action_list_value__ijMh2')]"
        device_labels = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, device_list_xpath))
        )
        for label in device_labels:
            name = driver.execute_script("return arguments[0].textContent;", label).strip()
            devices.append(name)
            logger.info(f"Found device: '{name}'")
        found_device_list = True

        # Cancel the dialog so it doesn't interfere
        try:
            alt_dialog = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'DeviceDialogBox-module_container')]")
                    )
            )
            # Try various methods to find the cancel button
            try:
                # First try by ID
                cancel_button = alt_dialog.find_element(By.XPATH, ".//div[contains(@id, 'CANCEL')]")
            except:
                # Then try by text
                cancel_button = alt_dialog.find_element(By.XPATH, ".//div[.//span[text()='Cancel']]")
                
            driver.execute_script("arguments[0].click();", cancel_button)
            logger.info("Canceled temporary device dialog.")
        except Exception as e:
            logger.warning(f"Warning: Could not cancel the temporary dialog: {e}")
        break  # Use the first available book to extract the list.
    except Exception as e:
        logger.error(f"Skipping a book while extracting device list: {e}")
        continue

if not found_device_list or not devices:
    logger.error("❌ Could not extract any devices. Exiting.")
    driver.quit()
    exit(1)

# -------------------------------
# Use Tkinter to Prompt the User for Device Selection
# -------------------------------
def select_device(devices_list, browser_window):
    root = tk.Tk()
    root.title("Select a Device")
    root.geometry("350x250")
    root.attributes("-topmost", True)
    
    # Position dialog in center of browser window
    browser_x = browser_window.get_window_position()['x']
    browser_y = browser_window.get_window_position()['y']
    browser_width = browser_window.get_window_size()['width']
    browser_height = browser_window.get_window_size()['height']
    
    # Calculate center position
    x_pos = browser_x + (browser_width - 350) // 2
    y_pos = browser_y + (browser_height - 250) // 2
    
    # Set position
    root.geometry(f"+{x_pos}+{y_pos}")

    prompt_text = ("Choose the Kindle device that you want to be selected for all book downloads. "
                   "The downloads will be keyed to this device and won't work on any other device unless the DRM is removed.")
    tk.Label(root, text=prompt_text, wraplength=320, justify="center", font=("Arial", 10)).pack(pady=10)
    
    var = tk.StringVar(value=devices_list[0])
    for dev in devices_list:
        tk.Radiobutton(root, text=dev, variable=var, value=dev, font=("Arial", 10)).pack(anchor="w", padx=20)
    
    selected_device = [None]  # Use list to store the selection
    
    def submit():
        selected_device[0] = var.get()
        root.quit()
        root.destroy()  # Explicitly destroy the window

    def on_closing():
        if selected_device[0] is None:
            selected_device[0] = var.get()  # Get the current selection if closing without submit
        root.quit()
        root.destroy()  # Explicitly destroy the window

    submit_button = tk.Button(root, text="Submit", command=submit, font=("Arial", 10))
    submit_button.pack(pady=10)
    
    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Run the main loop
    root.mainloop()
    
    # If window was closed without selection, use the default
    if selected_device[0] is None:
        selected_device[0] = devices_list[0]
    
    # Ensure any remaining instances are destroyed
    try:
        root.destroy()
    except:
        pass
        
    return selected_device[0]

logger.info("\nDisplaying device selection dialog...")
target_device_name = select_device(devices, driver)
logger.info(f"Selected device: {target_device_name}")

# -------------------------------
# Determine total pages from the pagination div
# -------------------------------
try:
    pagination_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "pagination"))
    )
    page_items = pagination_div.find_elements(By.XPATH, ".//a[contains(@class, 'page-item')]")
    if page_items:
        total_pages = int(page_items[-1].text.strip())
    else:
        total_pages = 1
    logger.info(f"✅ Total pages found: {total_pages}")
    
    # Set end page based on command line args or default to total_pages
    end_page = args.end if args.end else total_pages
    if end_page > total_pages:
        end_page = total_pages
        logger.info(f"End page adjusted to {end_page} (maximum available)")
    else:
        logger.info(f"Will process up to page {end_page}")
        
except Exception as e:
    logger.error(f"⚠️ Could not determine total pages from pagination. Defaulting to 1 page. Error: {e}")
    total_pages = 1
    end_page = 1

# Print instructions about keyboard interrupt
print("\nPress Ctrl+C at any time to stop processing and see results summary.")

# -------------------------------
# Loop Through Each Page and Process Books
# -------------------------------
try:
    for page in range(start_page, end_page + 1):
        if not running:
            break
            
        logger.info(f"\n=== Processing Page {page} of {end_page} ===")
        page_url = f"https://www.amazon.com/hz/mycd/digital-console/contentlist/booksAll/?pageNumber={page}"
        driver.get(page_url)
        time.sleep(3)  # Allow the page to load

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'MORE_ACTION')]"))
            )
            all_more_actions = driver.find_elements(By.XPATH, "//div[contains(@id, 'MORE_ACTION')]")
            total_books = len(all_more_actions)
            logger.info(f"✅ Found {total_books} books on page {page}.")
            
            for i in range(total_books):
                if not running:
                    break
                    
                try:
                    more_actions_buttons = driver.find_elements(By.XPATH, "//div[contains(@id, 'MORE_ACTION')]")
                    book_button = more_actions_buttons[i]
                    book_row = book_button.find_element(By.XPATH, "./ancestor::tr")
                    title_element = book_row.find_element(By.XPATH, ".//div[contains(@class, 'digital_entity_title')]")
                    book_title = title_element.text.strip()
                    book_id = title_element.get_attribute("id").split("-")[-1]
                    logger.info(f"\n📥 Processing book {i+1} of {total_books} on page {page}: {book_title} (ID: {book_id})")
                    
                    # First check for library loan indicators (reverse order)
                    library_loan_indicators = book_row.find_elements(
                        By.XPATH, 
                        ".//div[contains(@class, 'information_row')]/span[contains(text(), 'Borrowed on') or contains(text(), 'Expired on') or contains(text(), 'Kindle digital library loan')]"
                    )
                    if library_loan_indicators:
                        logger.info(f"❌ Book '{book_title}' is a library loan. Skipping.")
                        skipped_books.append({
                            "title": book_title,
                            "id": book_id,
                            "page": page,
                            "position": i+1,
                            "reason": "Library loan"
                        })
                        book_stats["library_loans"] += 1
                        book_stats["total_processed"] += 1
                        continue

                    # Then check for unavailable title indicator
                    unavailable = book_row.find_elements(
                        By.XPATH, 
                        ".//div[contains(@class, 'information_row')]/span[contains(text(), 'This title is unavailable for download and transfer')]"
                    )
                    if unavailable:
                        logger.info(f"❌ Book '{book_title}' is unavailable for download and transfer. Skipping.")
                        skipped_books.append({
                            "title": book_title,
                            "id": book_id,
                            "page": page,
                            "position": i+1,
                            "reason": "Unavailable for download"
                        })
                        book_stats["unavailable"] += 1
                        book_stats["total_processed"] += 1
                        continue

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", book_button)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", book_button)
                    time.sleep(0.5)

                    # Click "Download & Transfer via USB" button for this book - UPDATED
                    if DEBUG:
                        logger.debug(f"Attempting to find and click Download & transfer option for '{book_title}'")
                    if not find_and_click_download_option(driver):
                        logger.error(f"Failed to click Download & transfer option for '{book_title}'. Skipping.")
                        skipped_books.append({
                            "title": book_title,
                            "id": book_id,
                            "page": page,
                            "position": i+1,
                            "reason": "Failed to click download button"
                        })
                        book_stats["errors"] += 1
                        book_stats["total_processed"] += 1
                        continue
                    logger.info(f"✅ Clicked 'Download & Transfer via USB' button for {book_title}.")
                    time.sleep(0.5)

                    # Wait for either the device list or an alternative dialog to appear
                    device_list_xpath = f"//ul[@id='download_and_transfer_list_{book_id}']//div[contains(@class, 'ActionList-module_action_list_value__ijMh2')]"
                    try:
                        device_labels = WebDriverWait(driver, 3).until(
                            EC.presence_of_all_elements_located((By.XPATH, device_list_xpath))
                        )
                    except TimeoutException:
                        try:
                            alt_dialog = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[contains(@class, 'DeviceDialogBox-module_container') and not(contains(@class, 'hidden'))]")
                                )
                            )
                            try:
                                # First try by ID
                                cancel_button = alt_dialog.find_element(By.XPATH, ".//div[contains(@id, 'CANCEL')]")
                            except:
                                # Then try by text
                                cancel_button = alt_dialog.find_element(By.XPATH, ".//div[.//span[text()='Cancel']]")
                                
                            driver.execute_script("arguments[0].click();", cancel_button)
                            logger.info(f"⚠️ Alternative dialog appeared for '{book_title}', canceled download.")
                            skipped_books.append({
                                "title": book_title,
                                "id": book_id,
                                "page": page,
                                "position": i+1,
                                "reason": "Alternative dialog appeared"
                            })
                            book_stats["errors"] += 1
                            book_stats["total_processed"] += 1
                            time.sleep(1)
                            continue
                        except Exception as alt_e:
                            logger.error(f"⚠️ Error handling alternative dialog for '{book_title}': {alt_e}")
                            skipped_books.append({
                                "title": book_title,
                                "id": book_id,
                                "page": page,
                                "position": i+1,
                                "reason": f"Error handling dialog: {alt_e}"
                            })
                            book_stats["errors"] += 1
                            book_stats["total_processed"] += 1
                            continue

                    # Select the user-chosen device from the list
                    selected = False
                    for label in device_labels:
                        device_name = label.text.strip()
                        if device_name == target_device_name:
                            logger.info(f"✅ Selecting device: {target_device_name}")
                            try:
                                radio_button = label.find_element(By.XPATH, "./preceding-sibling::div//input")
                                driver.execute_script("arguments[0].click();", radio_button)
                            except Exception as radio_e:
                                # Try alternative method to select the radio button
                                try:
                                    # Find the parent li element and click the radio span
                                    parent_li = label.find_element(By.XPATH, "./..")
                                    radio_span = parent_li.find_element(By.XPATH, ".//span[contains(@class, 'RadioButton-module_radio')]")
                                    driver.execute_script("arguments[0].click();", radio_span)
                                except Exception as radio_e2:
                                    logger.error(f"Error selecting radio button: {radio_e2}")
                                    skipped_books.append({
                                        "title": book_title,
                                        "id": book_id,
                                        "page": page,
                                        "position": i+1,
                                        "reason": f"Error selecting device: {radio_e2}"
                                    })
                                    book_stats["errors"] += 1
                                    book_stats["total_processed"] += 1
                                    continue
                            
                            selected = True
                            time.sleep(0.5)
                            break

                    if not selected:
                        logger.info(f"❌ Device '{target_device_name}' not found for '{book_title}' (ID: {book_id}). Skipping.")
                        skipped_books.append({
                            "title": book_title,
                            "id": book_id,
                            "page": page,
                            "position": i+1,
                            "reason": f"Device '{target_device_name}' not found"
                        })
                        book_stats["errors"] += 1
                        book_stats["total_processed"] += 1
                        continue

                    # Click the Confirm Download button - UPDATED
                    try:
                        confirm_button = find_confirm_button(driver, book_id)
                        driver.execute_script("arguments[0].click();", confirm_button)
                        logger.info(f"✅ Download initiated for '{book_title}'!")
                        successful_downloads += 1
                        book_stats["total_successful"] += 1
                        book_stats["total_processed"] += 1
                    except Exception as confirm_e:
                        logger.error(f"Error clicking confirm button: {confirm_e}")
                        skipped_books.append({
                            "title": book_title,
                            "id": book_id,
                            "page": page,
                            "position": i+1,
                            "reason": f"Error confirming download: {confirm_e}"
                        })
                        book_stats["errors"] += 1
                        book_stats["total_processed"] += 1
                        continue
                    
                    # Close Success Dialog if it appears
                    try:
                        success_dialog = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "notification-success"))
                        )
                        close_button = success_dialog.find_element(By.ID, "notification-close")
                        driver.execute_script("arguments[0].click();", close_button)
                        logger.info(f"✅ Success dialog closed for '{book_title}'")
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"⚠️ Success dialog did not appear or could not be closed for '{book_title}': {e}")

                except Exception as inner_e:
                    logger.error(f"⚠️ Error processing book {i+1} on page {page}: {inner_e}")
                    # Try to get the book title and ID even in case of error
                    try:
                        book_title_error = title_element.text.strip() if 'title_element' in locals() else "Unknown"
                        book_id_error = book_id if 'book_id' in locals() else "Unknown"
                        skipped_books.append({
                            "title": book_title_error,
                            "id": book_id_error,
                            "page": page,
                            "position": i+1,
                            "reason": f"Unexpected error: {inner_e}"
                        })
                    except:
                        skipped_books.append({
                            "title": "Unknown",
                            "id": "Unknown",
                            "page": page,
                            "position": i+1,
                            "reason": f"Unexpected error: {inner_e}"
                        })
                    book_stats["errors"] += 1
                    book_stats["total_processed"] += 1
                    continue

        except Exception as e:
            logger.error(f"⚠️ Error finding books on page {page}: {e}")

except Exception as e:
    logger.error(f"⚠️ Error in main processing loop: {e}")
finally:
    if not running:
        print_summary_and_exit(driver)
    else:
        print_summary_and_exit(driver)