import asyncio
import email
import imaplib
import os
import tempfile
from threading import Thread

import customtkinter as tk
import cv2
import requests
import yagmail
import yaml
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from customtkinter import filedialog

from cipher import *

DOWNLOADS = Path.home() / 'Downloads'


async def run_task(command):
    global loading_bar
    initialize()
    loading_bar = tk.CTkProgressBar(master=cipherer_buttons_frame,
                                    mode="indeterminate",
                                    width=300,
                                    indeterminate_speed=1.5)
    loading_bar.grid(row=0, column=0, padx=20, pady=24)
    loading_bar.start()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, command)
    loading_bar.destroy()


def asyncio_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def loading_screen(command):
    loop = asyncio.new_event_loop()
    thread = Thread(target=asyncio_thread, args=(loop,))
    thread.start()
    loop.call_soon_threadsafe(asyncio.create_task, run_task(command))


def select_file():
    global filename, upload_button
    filename = filedialog.askopenfilename()
    upload_button.configure(text=filename)


def tooltip_creator(widget, which_dget, message):
    return CTkToolTip(widget,
                      message=message,
                      bg_color=which_dget.cget("fg_color"),
                      border_color=which_dget.cget("border_color"),
                      border_width=which_dget.cget("border_width"),
                      corner_radius=which_dget.cget("corner_radius")
                      )


def get_email_flags(email_uid):
    result, flags = mail.uid('FETCH', email_uid, '(FLAGS)')
    if result == "OK":
        flags = flags[0].decode()
        if "\\Seen" in flags:
            return True
        else:
            return False
    else:
        CTkMessagebox(title="Error",
                      message="Error no. 1 encountered. Email me saying you got error 'no. 1'. The app is about to "
                              "quit. Sorry for the inconvenience.",
                      icon="info",
                      option_1="OK")
        app.destroy()


def edit_mail():
    seen = get_email_flags(latest_email_uid)
    make_read_unread.configure(image=image_setter[seen])
    mail.uid('STORE', latest_email_uid, setter[seen], "\\SEEN")
    make_read_unread_tooltip.configure(message=tooltip_dictionary[seen])
    loading_bar.destroy()


def reply_func():
    global reply
    reply_message = CTkMessagebox(title="Warning",
                                  message="Are you sure you want to proceed? If you proceed? The subject of the reply "
                                          "will be automatically set, so you can't change it.",
                                  icon="warning",
                                  option_1="OK",
                                  option_2="Cancel")
    if reply_message.get() == "OK":
        global to_label, text_entry, subject_entry, text_label, aarit_check, vihaan_check, vedant_check, exit_button, \
            update_button, back_button, send_button, exit_button_tooltip, update_button_tooltip, back_button_tooltip
        reply = True
        initialize()
        exit_button.destroy()
        exit_button_tooltip.destroy()
        update_button.destroy()
        update_button_tooltip.destroy()
        back_button.destroy()
        back_button_tooltip.destroy()
        exit_button = tk.CTkButton(master=button_frame,
                                   text="Exit",
                                   command=lambda: loading_screen(app.destroy))
        exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
        update_button = tk.CTkButton(master=button_frame,
                                     text="Check for updates",
                                     command=lambda: loading_screen(check_for_updates))
        update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
        back_button = tk.CTkButton(master=button_frame,
                                   text="Back",
                                   command=lambda: loading_screen(ok_function))
        back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
        text_label.grid(column=1, row=0, padx=(24, 12), pady=24)
        text_entry.grid(column=2, row=0, padx=12, pady=24)
        upload_button.grid(column=3, row=0, padx=(12, 24), pady=24)
        text_frame.grid(column=1, row=2, padx=24, pady=12)
        exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
        back_button.grid(column=3, row=0, padx=12, pady=24)
        update_button.grid(column=2, row=0, padx=12, pady=24)
        send_button.grid(column=4, row=0, padx=(12, 24), pady=24)
        button_frame.grid(column=1, row=3, padx=24, pady=(12, 24))
        app.bind("<Control-Return>", lambda e: loading_screen(send_email_real))
        loading_bar.destroy()
    else:
        ok_function()


def send_email_real():
    global my_credentials, my_list, reply, reply_to, reply_subject, attachment
    app.update()
    text_entry.update()
    if text_entry.get("1.0", "end-1c").strip() != "" and (my_list != [] or reply):
        yag = yagmail.SMTP(my_credentials["user"], my_credentials["password"])
        if filename == "":
            attachment = ""
        else:
            encrypted_image = encrypt_image(filename, my_credentials["ID"])
            temp = os.path.basename(filename)
            input_file_name = ''.join([e for e in cipher(os.path.splitext(temp)[0], my_credentials["ID"]) if e not in (
                "<",
                ">",
                ":",
                "\"",
                "/",
                "\\",
                "|",
                "?",
                "*")]
                                      )
            input_file_name += '.png'
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                encrypted_image.save(tmp_file, format='PNG')
                tmp_file_path = tmp_file.name

            attachment = os.path.join(tempfile.gettempdir(), input_file_name)
            if os.path.exists(attachment):
                os.remove(attachment)
            os.rename(tmp_file_path, attachment)

        if not reply:
            yag.send(to=my_list, subject=cipher(("***" + subject_entry.get()), my_credentials["ID"]),
                     contents=[cipher(text_entry.get("1.0", "end-1c"), my_credentials["ID"]), attachment])
        elif reply:
            yag.send(to=reply_to, subject=cipher(reply_subject, my_credentials["ID"]),
                     contents=[cipher(text_entry.get("1.0", "end-1c"), my_credentials["ID"]), attachment])
        if os.path.exists(attachment):
            os.remove(attachment)
        ok_function()
    else:
        print(text_entry.get("1.0", "end-1c").strip())
        print(text_entry.get("1.0", "end-1c"))
        print(my_list)
        print(reply)
        CTkMessagebox(title="Error",
                      message="Please input something to send and choose who to send it to",
                      icon="warning",
                      option_1="Ok",
                      )
        send_email()
    loading_bar.destroy()


def checkbox_event():
    global my_list
    my_list = [e for e in [aarit_check.get(), vedant_check.get(), vihaan_check.get()] if e != 0]
    print(my_list)


def send_email():
    global to_label, text_entry, subject_entry, text_label, aarit_check, vihaan_check, vedant_check, exit_button, \
        update_button, back_button, send_button, exit_button_tooltip, update_button_tooltip, back_button_tooltip, \
        loading_bar
    initialize()
    exit_button.destroy()
    exit_button_tooltip.destroy()
    update_button.destroy()
    update_button_tooltip.destroy()
    back_button.destroy()
    back_button_tooltip.destroy()
    exit_button = tk.CTkButton(master=button_frame,
                               text="Exit",
                               command=lambda: loading_screen(app.destroy))
    exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
    update_button = tk.CTkButton(master=button_frame,
                                 text="Check for updates",
                                 command=lambda: loading_screen(check_for_updates))
    update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
    back_button = tk.CTkButton(master=button_frame,
                               text="Back",
                               command=lambda: loading_screen(ok_function))
    back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
    to_label.grid(column=1, row=0, pady=(24, 12), padx=(24, 12))
    aarit_check.grid(column=2, row=0, pady=(24, 12), padx=12)
    vedant_check.grid(column=3, row=0, pady=(24, 12), padx=12)
    vihaan_check.grid(column=4, row=0, pady=(24, 12), padx=(12, 24))
    subject_entry.grid(column=2, row=0, padx=(12, 24), pady=24)
    text_label.grid(column=1, row=0, padx=(24, 12), pady=24)
    text_entry.grid(column=2, row=0, padx=12, pady=24)
    upload_button.grid(column=3, row=0, padx=(12, 24), pady=24)
    to_frame.grid(column=1, row=0, padx=24, pady=(24, 12))
    subject_label.grid(column=1, row=0, padx=(24, 12), pady=24)
    subject_frame.grid(column=1, row=1, padx=24, pady=12)
    text_frame.grid(column=1, row=2, padx=24, pady=12)
    exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
    back_button.grid(column=3, row=0, padx=12, pady=24)
    update_button.grid(column=2, row=0, padx=12, pady=24)
    send_button.grid(column=4, row=0, padx=(12, 24), pady=24)
    button_frame.grid(column=1, row=3, padx=24, pady=(12, 24))
    app.bind("<Control-Return>", lambda e: loading_screen(send_email_real))
    app.bind("<Shift-Control-d>", lambda e: ok_function())
    loading_bar.destroy()


def ok_function():
    global check_gmail, exit_button, update_button
    initialize()
    compose.grid(column=1, row=0, pady=(24, 12), padx=24)
    check_gmail.grid(column=1, row=1, pady=12, padx=24)
    update_button.grid(column=1, row=2, pady=12, padx=24)
    exit_button.grid(column=1, row=3, pady=(12, 24), padx=24)
    loading_bar.destroy()


def check_gmail_function():
    global reply_subject, reply_to, exit_button, update_button, back_button, email_from, subject, body, final, mail, \
        latest_email_uid, exit_button_tooltip, update_button_tooltip, back_button_tooltip
    initialize()
    output.configure(state="normal")
    result, data = mail.uid('search', None, "UNSEEN")
    final = data[0].split()
    i = len(data[0].split())
    for x in range(i):
        latest_email_uid = data[0].split()[x]
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
        for part in (email_message.walk()):
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                subject = decipher(subject, my_credentials["ID"])
                if "***" not in subject or email_from not in ['"gandhv2@wis.edu.hk" <gandhv2@wis.edu.hk>',
                                                              '"gandhv3@wis.edu.hk" <gandhv3@wis.edu.hk>',
                                                              '"jaina10@wis.edu.hk" <jaina10@wis.edu.hk>']:
                    final.pop(final.index(data[0].split()[x]))
        mail.uid('STORE', latest_email_uid, '-FLAGS', "\\SEEN")
    if len(final) == 0:
        final.append(b'')
    if not final[0].split():
        output.insert(text="There is no unread email to decipher.",
                      index="1.0")
        output.configure(state="disabled")
        output.update()
        exit_button.destroy()
        exit_button_tooltip.destroy()
        update_button.destroy()
        update_button_tooltip.destroy()
        back_button.destroy()
        back_button_tooltip.destroy()
        exit_button = tk.CTkButton(master=button_frame,
                                   text="Exit",
                                   command=lambda: loading_screen(app.destroy))
        exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
        update_button = tk.CTkButton(master=button_frame,
                                     text="Check for updates",
                                     command=lambda: loading_screen(check_for_updates))
        update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
        back_button = tk.CTkButton(master=button_frame,
                                   text="Back",
                                   command=lambda: loading_screen(ok_function))
        back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
        output.grid(column=1, row=0, pady=(24, 12), padx=24)
        exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
        back_button.grid(column=3, row=0, padx=12, pady=24)
        update_button.grid(column=2, row=0, padx=12, pady=24)
        button_frame.grid(column=1, row=1, pady=(12, 24), padx=24)
    else:
        latest_email_uid = final[0]
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
        for part in (email_message.walk()):
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                subject = decipher(subject, my_credentials["ID"])
            if part.get_content_type() == "image/png":
                temp_filename = decipher(os.path.splitext(part.get_filename())[0], my_credentials["ID"])
                temp_filename += os.path.splitext(part.get_filename())[1]
                tmp_file_path = os.path.join(tempfile.gettempdir(), temp_filename)
                with open(tmp_file_path, 'wb') as tmp_file:
                    tmp_file.write(part.get_payload(decode=True))
                    tmp_file.flush()
                    decrypted_image = decrypt_image(tmp_file_path, my_credentials["ID"])
                    decrypted_image.save(tmp_file_path, format='PNG')
                    image = cv2.imread(tmp_file_path)
                    app.lift()
                    cv2.imshow(temp_filename, image)
        mail.uid('STORE', latest_email_uid, '+FLAGS', "\\SEEN")
        output.insert(text=("From: " + email_dictionary[email_from] + "\n\nSubject: " +
                            subject.replace("***", "") + "\n\n" +
                            decipher(body.decode('utf-8'), my_credentials["ID"]).__str__()),
                      index="1.0")
        reply_subject = subject
        reply_to = reply_email_dictionary[email_from]
        output.configure(state="disabled")
        output.update()
        exit_button.destroy()
        exit_button_tooltip.destroy()
        update_button.destroy()
        update_button_tooltip.destroy()
        back_button.destroy()
        back_button_tooltip.destroy()
        exit_button = tk.CTkButton(master=button_frame,
                                   text="Exit",
                                   command=lambda: loading_screen(app.destroy))
        exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
        update_button = tk.CTkButton(master=button_frame,
                                     text="Check for updates",
                                     command=lambda: loading_screen(check_for_updates))
        update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
        back_button = tk.CTkButton(master=button_frame,
                                   text="Back",
                                   command=lambda: loading_screen(ok_function))
        back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
        output.grid(column=1, row=0, pady=(24, 12), padx=(24, 12))
        exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
        back_button.grid(column=3, row=0, padx=12, pady=24)
        update_button.grid(column=2, row=0, padx=12, pady=24)
        reply_button.grid(column=4, row=0, padx=(12, 24), pady=24)
        make_read_unread.grid(column=2, row=0, pady=24, padx=(12, 24))
        button_frame.grid(column=1, row=1, pady=(12, 24), padx=24)
    app.bind("<Alt-e>", lambda e: hider())
    app.bind("<Escape>", lambda e: app.destroy())
    loading_bar.destroy()


def initialize():
    global cipherer_buttons_frame, check_gmail, exit_button, update_button, output, compose, to_label, \
        subject_entry, text_entry, text_label, vihaan_check, vedant_check, aarit_check, to_frame, text_frame, \
        subject_frame, back_button, send_button, button_frame, reply_button, subject_label, make_read_unread, \
        make_read_unread_tooltip, compose_tooltip, check_gmail_tooltip, aarit_check_tooltip, vedant_check_tooltip, \
        vihaan_check_tooltip, exit_button_tooltip, send_button_tooltip, reply_button_tooltip, update_button_tooltip, \
        back_button_tooltip, mail, upload_button, upload_picture, filename, attachment, loading_bar
    upload_button.destroy()
    compose.destroy()
    back_button.destroy()
    output.destroy()
    check_gmail.destroy()
    exit_button.destroy()
    update_button.destroy()
    text_label.destroy()
    vedant_check.destroy()
    vihaan_check.destroy()
    aarit_check.destroy()
    to_frame.destroy()
    text_frame.destroy()
    subject_frame.destroy()
    send_button.destroy()
    button_frame.destroy()
    reply_button.destroy()
    subject_label.destroy()
    make_read_unread.destroy()
    make_read_unread_tooltip.destroy()
    compose_tooltip.destroy()
    check_gmail_tooltip.destroy()
    aarit_check_tooltip.destroy()
    vedant_check_tooltip.destroy()
    vihaan_check_tooltip.destroy()
    exit_button_tooltip.destroy()
    send_button_tooltip.destroy()
    reply_button_tooltip.destroy()
    update_button_tooltip.destroy()
    back_button_tooltip.destroy()
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(my_credentials["user"], my_credentials["password"])
    mail.list()
    mail.select('inbox')
    to_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                           border_color=app.cget("color"))
    subject_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                                border_color=app.cget("color"))
    text_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                             border_color=app.cget("color"))
    button_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                               border_color=app.cget("color"))
    check_gmail = tk.CTkButton(master=cipherer_buttons_frame,
                               text="Check Gmail",
                               command=lambda: loading_screen(check_gmail_function))
    check_gmail_tooltip = tooltip_creator(check_gmail, check_gmail, "Check for New Emails")
    exit_button = tk.CTkButton(master=cipherer_buttons_frame,
                               text="Exit",
                               command=lambda: loading_screen(app.destroy))
    exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
    update_button = tk.CTkButton(master=cipherer_buttons_frame,
                                 text="Check for updates",
                                 command=lambda: loading_screen(check_for_updates))
    update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
    output = tk.CTkTextbox(master=cipherer_buttons_frame,
                           width=666,
                           height=333,
                           wrap="word")
    compose = tk.CTkButton(master=cipherer_buttons_frame,
                           text="Compose",
                           command=lambda: loading_screen(send_email))
    compose_tooltip = tooltip_creator(compose, compose, "Create a New Email")
    to_label = tk.CTkLabel(master=to_frame,
                           text="To: ")
    subject_entry = tk.CTkEntry(master=subject_frame,
                                placeholder_text="Subject",
                                width=333)
    text_entry = tk.CTkTextbox(master=text_frame,
                               width=333,
                               height=111,
                               wrap="word")
    text_label = tk.CTkLabel(master=text_frame,
                             text="Text: ")
    vedant_check = tk.CTkCheckBox(master=to_frame,
                                  text="Vedant",
                                  onvalue="gandhv2@wis.edu.hk",
                                  command=checkbox_event)
    vedant_check_tooltip = tooltip_creator(vedant_check, exit_button, "Send to Vedant")
    vihaan_check = tk.CTkCheckBox(master=to_frame,
                                  text="Vihaan",
                                  onvalue="gandhv3@wis.edu.hk",
                                  command=checkbox_event)
    vihaan_check_tooltip = tooltip_creator(vihaan_check, exit_button, "Send to Vihaan")
    aarit_check = tk.CTkCheckBox(master=to_frame,
                                 text="Aarit",
                                 onvalue="jaina10@wis.edu.hk",
                                 command=checkbox_event)
    aarit_check_tooltip = tooltip_creator(aarit_check, exit_button, "Send to Aarit")
    back_button = tk.CTkButton(master=cipherer_buttons_frame,
                               text="Back",
                               command=lambda: loading_screen(ok_function))
    back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
    send_button = tk.CTkButton(master=button_frame,
                               text="Send",
                               command=lambda: loading_screen(send_email_real))
    send_button_tooltip = tooltip_creator(send_button, send_button, "Send Email")
    reply_button = tk.CTkButton(master=button_frame,
                                text="Reply",
                                command=lambda: loading_screen(reply_func))
    reply_button_tooltip = tooltip_creator(reply_button, reply_button, "Reply to Email")
    subject_label = tk.CTkLabel(master=subject_frame,
                                text="Subject: ")
    make_read_unread = tk.CTkButton(master=cipherer_buttons_frame,
                                    command=lambda: loading_screen(edit_mail),
                                    text="",
                                    image=make_unread,
                                    width=20,
                                    height=20,
                                    border_color=app.cget("color"),
                                    fg_color="transparent")
    make_read_unread_tooltip = tooltip_creator(make_read_unread,
                                               exit_button,
                                               "Mark as unread")
    upload_picture = tk.CTkImage(light_image=Image.open(f"{DOWNLOADS}\\upload-light.png"),
                                 dark_image=Image.open(f"{DOWNLOADS}\\upload-dark.png"))
    upload_button = tk.CTkButton(master=text_frame,
                                 text="",
                                 width=20,
                                 height=20,
                                 image=upload_picture,
                                 border_color=app.cget("color"),
                                 fg_color="transparent",
                                 command=lambda: loading_screen(select_file))

    filename = ""
    attachment = None


def check_for_updates():
    global my_credentials
    page = requests.get("https://raw.githubusercontent.com/AJ-cubes39/Cipherer-for-Windows/refs/heads/main/version.txt")
    if my_credentials["version"] == page.text and password_type == "User":
        CTkMessagebox(title="Up to Date", message="You are up to date!", icon="check", option_1="Close")
    elif my_credentials["version"] != page.text or password_type == "Admin":
        update_message = CTkMessagebox(title="Update available",
                                       message="There is an update available! If you choose to update, the app will "
                                               "restart. You may even be redirected to a google page for less than a "
                                               "second.",
                                       icon="info",
                                       option_1="Update",
                                       option_2="Not now")
        if update_message.get() == "Update":
            app.destroy()
            os.startfile(f"{DOWNLOADS}\\Updater.exe")
    else:
        CTkMessagebox(title="No Update",
                      message="There is no update available",
                      icon="check",
                      option_1="OK")
    loading_bar.destroy()


def hider():
    global app
    if app.winfo_viewable():
        app.update()
        app.iconify()


with open(f"{DOWNLOADS}\\credentials.yml") as f:
    content = f.read()
my_credentials = yaml.load(content, Loader=yaml.FullLoader)

tk.set_appearance_mode("System")
tk.FontManager.load_font(f"{DOWNLOADS}\\ctk_font.ttf")
tk.set_default_color_theme(f"{DOWNLOADS}\\ctk_theme.json")
app = tk.CTk()
app.wm_title("Cipherer")
app.bind("<Alt-e>", lambda e: hider())
app.bind("<Escape>", lambda e: app.destroy())

make_unread = tk.CTkImage(light_image=Image.open(f"{DOWNLOADS}\\unread-light.png"),
                          dark_image=Image.open(f"{DOWNLOADS}\\unread-dark.png"),
                          size=(35, 35))
make_read = tk.CTkImage(light_image=Image.open(f"{DOWNLOADS}\\read-light.png"),
                        dark_image=Image.open(f"{DOWNLOADS}\\read-dark.png"),
                        size=(35, 35))

title_frame = tk.CTkFrame(master=app)
title = tk.CTkLabel(master=title_frame,
                    text="Cipherer Program",
                    font=("ctk_font", 24))
title.grid(column=0, row=0, pady=(12, 24), padx=24)
version_label = tk.CTkLabel(master=title_frame,
                            text=("Version: " + my_credentials["version"]))
version_label.grid(column=0, row=1, pady=(0, 5), padx=24)

cipherer_buttons_frame = tk.CTkFrame(master=app)
to_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                       border_color=app.cget("color"))
subject_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                            border_color=app.cget("color"))
text_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                         border_color=app.cget("color"))
button_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                           border_color=app.cget("color"))

compose = tk.CTkButton(master=cipherer_buttons_frame,
                       text="Compose",
                       command=lambda: loading_screen(send_email))
compose.grid(column=1, row=0, pady=(24, 12), padx=24)
compose_tooltip = tooltip_creator(compose, compose, "Create a New Email")
check_gmail = tk.CTkButton(master=cipherer_buttons_frame,
                           text="Check Gmail",
                           command=lambda: loading_screen(check_gmail_function))
check_gmail.grid(column=1, row=1, pady=12, padx=24)
check_gmail_tooltip = tooltip_creator(check_gmail, check_gmail, "Check for New Emails")
exit_button = tk.CTkButton(master=cipherer_buttons_frame,
                           text="Exit",
                           command=lambda: loading_screen(app.destroy))
exit_button.grid(column=1, row=3, pady=(12, 24), padx=24)
exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
update_button = tk.CTkButton(master=cipherer_buttons_frame,
                             text="Check for updates",
                             command=lambda: loading_screen(check_for_updates))
update_button.grid(column=1, row=2, pady=12, padx=24)
app.bind("<Control-u>", lambda e: check_for_updates())
update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
output = tk.CTkTextbox(master=cipherer_buttons_frame,
                       width=666,
                       height=333,
                       wrap="word")
to_label = tk.CTkLabel(master=to_frame,
                       text="To: ")
text_label = tk.CTkLabel(master=text_frame,
                         text="Text: ")
subject_entry = tk.CTkEntry(master=subject_frame,
                            placeholder_text="Subject",
                            width=333)
text_entry = tk.CTkTextbox(master=text_frame,
                           width=333,
                           height=111,
                           wrap="word")
upload_picture = tk.CTkImage(light_image=Image.open(f"{DOWNLOADS}\\upload-light.png"),
                             dark_image=Image.open(f"{DOWNLOADS}\\upload-dark.png"))
upload_button = tk.CTkButton(master=text_frame,
                             text="",
                             width=20,
                             height=20,
                             image=upload_picture,
                             border_color=app.cget("color"),
                             fg_color="transparent",
                             command=lambda: loading_screen(select_file))
vedant_check = tk.CTkCheckBox(master=to_frame,
                              text="Vedant",
                              onvalue="gandhv2@wis.edu.hk",
                              command=checkbox_event)
vedant_check_tooltip = tooltip_creator(vedant_check, exit_button, "Send to Vedant")
vihaan_check = tk.CTkCheckBox(master=to_frame,
                              text="Vihaan",
                              onvalue="gandhv3@wis.edu.hk",
                              command=checkbox_event)
vihaan_check_tooltip = tooltip_creator(vihaan_check, exit_button, "Send to Vihaan")
aarit_check = tk.CTkCheckBox(master=to_frame,
                             text="Aarit",
                             onvalue="jaina10@wis.edu.hk",
                             command=checkbox_event)
aarit_check_tooltip = tooltip_creator(aarit_check, exit_button, "Send to Aarit")
back_button = tk.CTkButton(master=cipherer_buttons_frame,
                           text="Back",
                           command=lambda: loading_screen(ok_function))
back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
send_button = tk.CTkButton(master=button_frame,
                           text="Send",
                           command=lambda: loading_screen(send_email_real))
send_button_tooltip = tooltip_creator(send_button, send_button, "Send Email")
reply_button = tk.CTkButton(master=button_frame,
                            text="Reply",
                            command=lambda: loading_screen(reply_func))
reply_button_tooltip = tooltip_creator(reply_button, reply_button, "Reply to Email")
subject_label = tk.CTkLabel(master=subject_frame,
                            text="Subject: ")
make_read_unread = tk.CTkButton(master=cipherer_buttons_frame,
                                command=lambda: loading_screen(edit_mail),
                                text="",
                                image=make_unread,
                                width=20,
                                height=20,
                                border_color=app.cget("color"),
                                fg_color="transparent")
make_read_unread_tooltip = tooltip_creator(make_read_unread,
                                           exit_button,
                                           "Mark as unread")
loading_bar = tk.CTkProgressBar(master=cipherer_buttons_frame,
                                mode="indeterminate",
                                width=300,
                                indeterminate_speed=1.5)

title_frame.pack(pady=12, padx=24)
cipherer_buttons_frame.pack(pady=12, padx=24)

email_dictionary = {'"jaina10@wis.edu.hk" <jaina10@wis.edu.hk>': "Aarit",
                    '"gandhv3@wis.edu.hk" <gandhv3@wis.edu.hk>': "Vihaan",
                    '"gandhv2@wis.edu.hk" <gandhv2@wis.edu.hk>': "Vedant"}
reply_email_dictionary = {'"jaina10@wis.edu.hk" <jaina10@wis.edu.hk>': "jaina10@wis.edu.hk",
                          '"gandhv3@wis.edu.hk" <gandhv3@wis.edu.hk>': "gandhv3@wis.edu.hk",
                          '"gandhv2@wis.edu.hk" <gandhv2@wis.edu.hk>': "gandhv2@wis.edu.hk"}
setter = {True: "-FLAGS",
          False: "+FLAGS"}
image_setter = {True: make_read,
                False: make_unread}
tooltip_dictionary = {True: "Mark as read",
                      False: "Mark as unread"}

my_list = []
final = []
reply_subject = ""
reply_to = ""
email_from = ""
subject = ""
body = ""
latest_email_uid = ""
filename = ""
reply = False
attachment = None

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(my_credentials["user"], my_credentials["password"])
mail.list()
mail.select('inbox')

if my_credentials["state"] == "zoomed":
    app.state("zoomed")
elif my_credentials["state"] == "fullscreen":
    app.geometry("1920x1080+-10+-10")

app.mainloop()
