import email
import imaplib
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import webbrowser
from threading import Thread
from tkinter import Event

import customtkinter as tk
import requests
import yagmail
import yaml
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from customtkinter import filedialog

import cipher
from cipher import *


def theme_command():
    my_credentials["theme"] = "Dark" if my_credentials["theme"] == "Light" else "Light"
    with open("credentials.yml", "w") as ffile:
        yaml.dump(my_credentials, ffile)
    tk.set_appearance_mode(my_credentials["theme"])
    button_tooltip.configure(message=f"Switch to {"Dark" if my_credentials["theme"] == "Light" else "Light"} Mode")


def importer():
    import main
    main.useless = None


def logout():
    my_credentials["remember_me_overrule"] = True
    with open(f"credentials.yml", "w") as file:
        yaml.dump(my_credentials, file)
    app.destroy()
    threading.Thread(target=importer).start()
    sys.exit()


def get_unique_urls():
    history_path = os.path.expanduser('~') + "/AppData/Local/Google/Chrome/User Data/Default/History"
    temp_history_path = os.path.expanduser('~') + "/AppData/Local/Google/Chrome/User Data/Default/History_copy"
    if not os.path.exists(history_path):
        return []

    try:
        shutil.copy2(history_path, temp_history_path)
        connection = sqlite3.connect(temp_history_path)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT url FROM urls")
        results = cursor.fetchall()
        urls_list = [url[0].rstrip("/") for url in results]
        connection.close()
        return urls_list

    except sqlite3.OperationalError:
        return []


def open_link(event):
    widget = event.widget
    index = widget.index("@{},{}".format(event.x, event.y))
    for tag in widget.tag_names(index):
        if tag.startswith("link"):
            url = widget.get(widget.tag_ranges(tag)[0], widget.tag_ranges(tag)[1])
            webbrowser.open_new(url)
            break


def detect_links(event):
    text = event.widget.get("1.0", "end-1c")
    event.widget.tag_remove("link", "1.0", "end")

    url_pattern = r"https?://[^\s]+"
    urls = re.finditer(url_pattern, text)

    for i, match in enumerate(urls):
        start_index = "1.0 + {} chars".format(match.start())
        end_index = "1.0 + {} chars".format(match.end())
        tag_name = f"link{i}"
        event.widget.tag_add(tag_name, start_index, end_index)
        if match.group().rstrip("/") not in get_unique_urls():
            event.widget.tag_config(tag_name, foreground='#0066CC', underline=True)
        else:
            event.widget.tag_config(tag_name, foreground='#551A8B', underline=True)
        event.widget.tag_bind(tag_name, "<Button-1>", open_link)
        event.widget.tag_bind(tag_name, "<Enter>", lambda e: event.widget.configure(cursor="hand2"))
        event.widget.tag_bind(tag_name, "<Leave>", lambda e: event.widget.configure(cursor="ibeam"))


def start_updater():
    global my_credentials
    page = requests.get("https://raw.githubusercontent.com/AJ-cubes39/"
                        "Cipherer-for-Windows/refs/heads/main/version.txt",
                        headers={"Authorization": "token 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"}).text
    if my_credentials["version"] != page:
        message = requests.get("https://raw.githubusercontent.com/AJ-cubes39/Cipherer-for-Windows/refs/heads/main"
                               "/What's%20New",
                               headers={"Authorization": "token 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"}).text
        update_message = CTkMessagebox(title=f"Version {page.strip()} available.",
                                       message=message,
                                       icon="info",
                                       option_1="Update",
                                       option_2="Not now")
        if update_message.get() == "Update":
            app.destroy()
            if not os.path.exists(f"Updater.exe"):
                with open(f"Updater.exe", "wb") as file:
                    request = requests.get("https://www.dropbox.com/scl/fi/hxqtxb42plyo8of6vjp80/Updater.txt?rlkey"
                                           "=oyua94cqci1xvcnjj5oi49jrd&st=wjcvhvge&dl=1")
                    file.write(request.content)
            os.startfile(f"Updater.exe")
            sys.exit()


def textbox_ctrl_bs(event):
    ent = event.widget
    end_idx = ent.index(tk.INSERT)
    end_line, end_col = map(int, end_idx.split("."))
    start_idx = ent.get("1.0", end_idx).rfind(" ", None, end_col)
    ent.tag_add(tk.SEL, f"1.{start_idx}", end_idx)


def entry_ctrl_bs(event):
    ent = event.widget
    end_idx = ent.index(tk.INSERT)
    start_idx = ent.get().rfind(" ", None, end_idx)
    ent.selection_range(start_idx, end_idx)


def download_image(image_path, output_path):
    path = filedialog.askdirectory()
    output_path = path + output_path
    with open(image_path, "rb") as file:
        data = file.read()
    with open(output_path, "wb") as file:
        file.write(data)
    CTkMessagebox(title="Successful Download",
                  message=f"The image has been successfully downloaded to {output_path}",
                  icon="check",
                  option_1="OK!")


def resize_image(resized_image, max_width, max_height):
    width, height = resized_image.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        resized_image = resized_image.resize(new_size, Image.LANCZOS)
    return resized_image


def grid_forget():
    global cipherer_buttons_frame, check_gmail, exit_button, update_button, output, compose, to_label, \
        subject_entry, text_entry, text_label, vihaan_check, vedant_check, aarit_check, to_frame, text_frame, \
        subject_frame, back_button, send_button, button_frame, reply_button, subject_label, make_read_unread, \
        make_read_unread_tooltip, compose_tooltip, check_gmail_tooltip, aarit_check_tooltip, vedant_check_tooltip, \
        vihaan_check_tooltip, exit_button_tooltip, send_button_tooltip, reply_button_tooltip, update_button_tooltip, \
        back_button_tooltip, mail, upload_button, upload_picture, filename, attachment, loading_bar, retry_button
    upload_button.grid_forget()
    compose.grid_forget()
    back_button.grid_forget()
    output.grid_forget()
    check_gmail.grid_forget()
    exit_button.grid_forget()
    update_button.grid_forget()
    text_label.grid_forget()
    vedant_check.grid_forget()
    vihaan_check.grid_forget()
    aarit_check.grid_forget()
    to_frame.grid_forget()
    text_frame.grid_forget()
    subject_frame.grid_forget()
    send_button.grid_forget()
    button_frame.grid_forget()
    reply_button.grid_forget()
    subject_label.grid_forget()
    make_read_unread.grid_forget()
    retry_button.grid_forget()


def loading_screen(command):
    global loading_bar

    def callback():
        command()
        loading_bar.destroy()

    thread = Thread(target=callback)
    thread.start()
    grid_forget()
    loading_bar = tk.CTkProgressBar(master=cipherer_buttons_frame,
                                    mode="indeterminate",
                                    width=300,
                                    indeterminate_speed=1.5)
    loading_bar.grid(row=0, column=0, padx=20, pady=24)
    loading_bar.start()
    return 'break'


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
    return None


def edit_mail():
    seen = get_email_flags(latest_email_uid)
    make_read_unread.configure(image=image_setter[seen])
    mail.uid('STORE', latest_email_uid, setter[seen], "\\SEEN")
    make_read_unread_tooltip.configure(message=tooltip_dictionary[seen])


def reply_func():
    global to_label, text_entry, subject_entry, text_label, aarit_check, vihaan_check, vedant_check, exit_button, \
        update_button, back_button, send_button, exit_button_tooltip, update_button_tooltip, back_button_tooltip, reply
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
                               command=app.destroy)
    exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
    update_button = tk.CTkButton(master=button_frame,
                                 text="Check for updates",
                                 command=check_for_updates)
    update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
    back_button = tk.CTkButton(master=button_frame,
                               text="Back",
                               command=ok_function)
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
    text_entry.bind("<Control-Return>", lambda e: loading_screen(send_email_real))
    text_entry.bind("<KeyRelease>", detect_links)
    text_entry.bind('<Control-BackSpace>', textbox_ctrl_bs)
    app.bind("<Alt-Left>", lambda e: ok_function())


def send_email_real():
    global my_credentials, my_list, reply, reply_to, reply_subject, attachment, tmp_file_path
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
        CTkMessagebox(title="Error",
                      message="Please input something to send and choose who to send it to",
                      icon="warning",
                      option_1="Ok",
                      )
        send_email()


def checkbox_event():
    global my_list
    my_list = [e for e in [aarit_check.get(), vedant_check.get(), vihaan_check.get()] if e != 0]


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
                               command=app.destroy)
    exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
    update_button = tk.CTkButton(master=button_frame,
                                 text="Check for updates",
                                 command=check_for_updates)
    update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
    back_button = tk.CTkButton(master=button_frame,
                               text="Back",
                               command=ok_function)
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
    text_entry.bind("<Control-Return>", lambda e: loading_screen(send_email_real))
    app.bind("<Shift-Control-d>", lambda e: ok_function())
    text_entry.bind("<KeyRelease>", detect_links)
    text_entry.bind('<Control-BackSpace>', textbox_ctrl_bs)
    subject_entry.bind('<Control-BackSpace>', entry_ctrl_bs)
    app.bind("<Alt-Left>", lambda e: ok_function())


def ok_function():
    global check_gmail, exit_button, update_button
    initialize()
    compose.grid(column=1, row=0, pady=(24, 12), padx=24)
    check_gmail.grid(column=1, row=1, pady=12, padx=24)
    update_button.grid(column=1, row=2, pady=12, padx=24)
    exit_button.grid(column=1, row=3, pady=(12, 24), padx=24)


def check_gmail_function():
    global reply_subject, reply_to, exit_button, update_button, back_button, email_from, subject, body, final, mail, \
        latest_email_uid, exit_button_tooltip, update_button_tooltip, back_button_tooltip, tmp_file_path, \
        temp_filename, image, image_button, download_button, image_button_tooltip, download_button_tooltip
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
                                   command=app.destroy)
        exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
        update_button = tk.CTkButton(master=button_frame,
                                     text="Check for updates",
                                     command=check_for_updates)
        update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
        back_button = tk.CTkButton(master=button_frame,
                                   text="Back",
                                   command=ok_function)
        back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
        output.grid(column=1, row=0, pady=(24, 12), padx=24)
        exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
        retry_button.grid(column=3, row=0, padx=12, pady=24)
        back_button.grid(column=4, row=0, padx=(12, 24), pady=24)
        update_button.grid(column=2, row=0, padx=12, pady=24)
        button_frame.grid(column=1, row=1, pady=(12, 24), padx=24)
        app.bind("<Alt-Left>", lambda e: ok_function())
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
                image = True
                temp_filename = decipher(os.path.splitext(part.get_filename())[0], my_credentials["ID"])
                temp_filename += os.path.splitext(part.get_filename())[1]
                tmp_file_path = os.path.join(tempfile.gettempdir(), temp_filename)
                with open(tmp_file_path, 'wb') as tmp_file:
                    tmp_file.write(part.get_payload(decode=True))
                    tmp_file.flush()
                    decrypted_image = decrypt_image(tmp_file_path, my_credentials["ID"])
                    decrypted_image.save(tmp_file_path, format='PNG')
            elif part.get_content_type() != "image/png":
                image = False
        mail.uid('STORE', latest_email_uid, '+FLAGS', "\\SEEN")
        output.insert(text=f"From: {email_dictionary[email_from]}\n\nSubject: {subject.replace("***", "")}\n\n"
                           f"{decipher(body.decode('utf-8'), my_credentials["ID"]).__str__()}",
                      index="1.0")
        reply_subject = subject
        reply_to = reply_email_dictionary[email_from]
        output.configure(state="disabled")
        event = Event()
        event.widget = output
        detect_links(event)
        output.update()
        exit_button.destroy()
        exit_button_tooltip.destroy()
        update_button.destroy()
        update_button_tooltip.destroy()
        back_button.destroy()
        back_button_tooltip.destroy()
        exit_button = tk.CTkButton(master=button_frame,
                                   text="Exit",
                                   command=app.destroy)
        exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
        update_button = tk.CTkButton(master=button_frame,
                                     text="Check for updates",
                                     command=check_for_updates)
        update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
        back_button = tk.CTkButton(master=button_frame,
                                   text="Back",
                                   command=ok_function)
        back_button_tooltip = tooltip_creator(back_button, back_button, "Go Back")
        output.grid(column=1, row=0, pady=(24, 12), padx=(24, 12))
        exit_button.grid(column=1, row=0, padx=(24, 12), pady=24)
        back_button.grid(column=3, row=0, padx=12, pady=24)
        update_button.grid(column=2, row=0, padx=12, pady=24)
        retry_button.grid(column=4, row=0, padx=12, pady=24)
        reply_button.grid(column=5, row=0, padx=(12, 24), pady=24)
        make_read_unread.grid(column=2, row=0, pady=24, padx=(12, 24))
        button_frame.grid(column=1, row=2, pady=(12, 24), padx=(24, 0))
        app.bind("<Alt-Left>", lambda e: ok_function())
        if image:
            image_frame = tk.CTkFrame(master=cipherer_buttons_frame,
                                      border_color=app.cget("fg_color"))
            test_image = Image.open(tmp_file_path)
            test_image = resize_image(test_image, 50, 50)
            photo = tk.CTkImage(light_image=test_image,
                                dark_image=test_image,
                                size=test_image.size)
            image_button = tk.CTkButton(master=image_frame,
                                        command=lambda: os.startfile(tmp_file_path),
                                        fg_color="transparent",
                                        text=f"Open \"{temp_filename}\": ",
                                        image=photo,
                                        border_color=app.cget("fg_color"),
                                        compound='right')
            image_button_tooltip = tooltip_creator(image_button, image_button, "Open Image")
            image_button.grid(column=2, row=1)
            download_image_button = tk.CTkImage(light_image=Image.open(f"download-light.png"),
                                                dark_image=Image.open(f"download-dark.png"))
            download_button = tk.CTkButton(master=image_frame,
                                           command=lambda: download_image(tmp_file_path,
                                                                          f"\\{temp_filename}"),
                                           text="",
                                           width=20,
                                           height=20,
                                           image=download_image_button,
                                           fg_color="transparent",
                                           border_color=app.cget("fg_color"))
            download_button_tooltip = tooltip_creator(download_button, download_button, "Download Image")
            download_button.grid(column=3, row=1)
            image_frame.grid(column=1, row=1, pady=12)
    app.bind("<Alt-e>", lambda e: hider())
    app.bind("<Escape>", lambda e: sys.exit())
    app.bind("<Control-r>", lambda e: loading_screen(check_gmail_function))
    app.lift()


def initialize():
    global cipherer_buttons_frame, check_gmail, exit_button, update_button, output, compose, to_label, \
        subject_entry, text_entry, text_label, vihaan_check, vedant_check, aarit_check, to_frame, text_frame, \
        subject_frame, back_button, send_button, button_frame, reply_button, subject_label, make_read_unread, \
        make_read_unread_tooltip, compose_tooltip, check_gmail_tooltip, aarit_check_tooltip, vedant_check_tooltip, \
        vihaan_check_tooltip, exit_button_tooltip, send_button_tooltip, reply_button_tooltip, update_button_tooltip, \
        back_button_tooltip, mail, upload_button, upload_picture, filename, attachment, loading_bar, \
        image_button, download_button, retry_button, upload_button_tooltip, retry_button_tooltip, \
        image_button_tooltip, download_button_tooltip, suggestion_label, match_dict
    image_button.destroy()
    download_button.destroy()
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
    retry_button.destroy()
    upload_button_tooltip.destroy()
    retry_button_tooltip.destroy()
    image_button_tooltip.destroy()
    download_button_tooltip.destroy()
    suggestion_label.destroy()
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(my_credentials["user"], my_credentials["password"])
    mail.list()
    mail.select('"[Gmail]/All Mail"')
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
                               command=app.destroy)
    exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
    update_button = tk.CTkButton(master=cipherer_buttons_frame,
                                 text="Check for updates",
                                 command=check_for_updates)
    update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
    output = tk.CTkTextbox(master=cipherer_buttons_frame,
                           width=666,
                           height=333,
                           wrap="word",
                           activate_scrollbars=True)
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
                               command=ok_function)
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
                                    command=edit_mail,
                                    text="",
                                    image=make_unread,
                                    width=20,
                                    height=20,
                                    border_color=app.cget("color"),
                                    fg_color="transparent")
    make_read_unread_tooltip = tooltip_creator(make_read_unread,
                                               exit_button,
                                               "Mark as unread")
    upload_picture = tk.CTkImage(light_image=Image.open(f"upload-light.png"),
                                 dark_image=Image.open(f"upload-dark.png"))
    upload_button = tk.CTkButton(master=text_frame,
                                 text="",
                                 width=20,
                                 height=20,
                                 image=upload_picture,
                                 border_color=app.cget("color"),
                                 fg_color="transparent",
                                 command=select_file)
    upload_button_tooltip = tooltip_creator(upload_button, upload_button, "Upload Image")
    retry_button = tk.CTkButton(master=button_frame,
                                text="Retry",
                                command=lambda: loading_screen(check_gmail_function))
    retry_button_tooltip = tooltip_creator(retry_button, retry_button, "Retry Check Gmail")
    suggestion_label = tk.CTkLabel(master=text_frame,
                                   text="")

    match_dict = {}

    filename = ""

    attachment = None


def check_for_updates():
    global my_credentials
    page = requests.get("https://raw.githubusercontent.com/AJ-cubes39/"
                        "Cipherer-for-Windows/refs/heads/main/version.txt",
                        headers={"Authorization": "token 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"}).text
    if my_credentials["version"] == page and password_type == "User":
        CTkMessagebox(title="Up to Date", message="You are up to date!", icon="check", option_1="Close")
    elif my_credentials["version"] != page or password_type == "Admin":
        message = requests.get("https://raw.githubusercontent.com/AJ-cubes39/Cipherer-for-Windows/refs/heads/main"
                               "/What's%20New",
                               headers={"Authorization": "token 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"}).text
        update_message = CTkMessagebox(title=f"Version {page.strip()} available.",
                                       message=message,
                                       icon="info",
                                       option_1="Update",
                                       option_2="Not now")
        if update_message.get() == "Update":
            app.destroy()
            if not os.path.exists(f"Updater.exe"):
                with open(f"Updater.exe", "wb") as file:
                    request = requests.get("https://www.dropbox.com/scl/fi/hxqtxb42plyo8of6vjp80/Updater.txt?rlkey"
                                           "=oyua94cqci1xvcnjj5oi49jrd&st=wjcvhvge&dl=1",)
                    file.write(request.content)
            os.startfile(f"Updater.exe")
            sys.exit()


def hider():
    global app
    if app.winfo_viewable():
        app.update()
        app.iconify()


with open(f"credentials.yml") as f:
    content = f.read()
my_credentials = yaml.load(content, Loader=yaml.FullLoader)

tk.set_appearance_mode(my_credentials["theme"])
tk.FontManager.load_font(f"ctk_font.ttf")
tk.set_default_color_theme(f"ctk_theme.json")

app = tk.CTk()
app.wm_title("Cipherer")
app.bind("<Alt-e>", lambda e: hider())
app.bind("<Escape>", lambda e: sys.exit())

make_unread = tk.CTkImage(light_image=Image.open(f"unread-light.png"),
                          dark_image=Image.open(f"unread-dark.png"),
                          size=(35, 35))
make_read = tk.CTkImage(light_image=Image.open(f"read-light.png"),
                        dark_image=Image.open(f"read-dark.png"),
                        size=(35, 35))

title_frame = tk.CTkFrame(master=app)
title = tk.CTkLabel(master=title_frame,
                    text="Cipherer Program",
                    font=("ctk_font", 24))
title.grid(column=0, row=0, pady=(12, 6), padx=24)
version_label = tk.CTkLabel(master=title_frame,
                            text=("Version: " + my_credentials["version"]))
version_label.grid(column=0, row=1, pady=(6, 5), padx=24)

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
                           command=app.destroy)
exit_button.grid(column=1, row=3, pady=(12, 24), padx=24)
exit_button_tooltip = tooltip_creator(exit_button, exit_button, "Close the Application")
update_button = tk.CTkButton(master=cipherer_buttons_frame,
                             text="Check for updates",
                             command=check_for_updates)
update_button.grid(column=1, row=2, pady=12, padx=24)
app.bind("<Control-u>", lambda e: check_for_updates())
update_button_tooltip = tooltip_creator(update_button, update_button, "Check for Software Updates")
output = tk.CTkTextbox(master=cipherer_buttons_frame,
                       width=666,
                       height=333,
                       wrap="word",
                       activate_scrollbars=True)
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
upload_picture = tk.CTkImage(light_image=Image.open(f"upload-light.png"),
                             dark_image=Image.open(f"upload-dark.png"))
upload_button = tk.CTkButton(master=text_frame,
                             text="",
                             width=20,
                             height=20,
                             image=upload_picture,
                             border_color=app.cget("color"),
                             fg_color="transparent",
                             command=select_file)
upload_button_tooltip = tooltip_creator(upload_button, upload_button, "Upload Image")
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
                           command=ok_function)
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
                                command=edit_mail,
                                text="",
                                image=make_unread,
                                width=20,
                                height=20,
                                border_color=app.cget("color"),
                                fg_color="transparent")
make_read_unread_tooltip = tooltip_creator(make_read_unread,
                                           exit_button,
                                           "Mark as unread")
retry_button = tk.CTkButton(master=button_frame,
                            text="Retry",
                            command=lambda: loading_screen(check_gmail_function))
retry_button_tooltip = tooltip_creator(retry_button, retry_button, "Retry Check Gmail")
loading_bar = tk.CTkProgressBar(master=cipherer_buttons_frame,
                                mode="indeterminate",
                                width=300,
                                indeterminate_speed=1.5)
image_button = tk.CTkButton(master=app)
image_button_tooltip = tooltip_creator(image_button, image_button, "Open Image")
download_button = tk.CTkButton(master=app)
download_button_tooltip = tooltip_creator(download_button, download_button, "Download Image")
suggestion_label = tk.CTkLabel(master=text_frame,
                               text="")
logout_image = tk.CTkImage(light_image=Image.open(f"logout-light.png"),
                           dark_image=Image.open(f"logout-dark.png"),
                           size=(30, 30))
logout = tk.CTkButton(master=app,
                      text="",
                      command=logout,
                      image=logout_image,
                      width=30,
                      height=30,
                      border_color=app.cget("color"),
                      fg_color="transparent")
logout.grid(column=2, row=0)
logout_tooltip = tooltip_creator(logout, exit_button, "Logout of the Application")
light = Image.open("light-mode.png")
dark = Image.open("dark-mode.png")
theme_image = tk.CTkImage(light_image=light,
                          dark_image=dark,
                          size=(37, 21))
button = tk.CTkButton(master=app,
                      command=theme_command,
                      image=theme_image,
                      text="",
                      bg_color="transparent",
                      fg_color="transparent",
                      border_color=app.cget("fg_color"),
                      width=37,
                      height=21)
button.grid(column=0, row=0)
button_tooltip = tooltip_creator(button,
                                 exit_button,
                                 f"Switch to {"Dark" if my_credentials["theme"] == "Light" else "Light"} Mode")


title_frame.grid(column=1, row=0, pady=(24, 12), padx=(24, 0))
cipherer_buttons_frame.grid(column=1, row=1, pady=(12, 24), padx=(24, 0))

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
match_dict = {}

my_list = []
final = []

reply_subject = ""
reply_to = ""
email_from = ""
subject = ""
body = ""
latest_email_uid = ""
filename = ""
temp_filename = ""
tmp_file_path = ""

reply = False
image = False
attachment = None

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(my_credentials["user"], my_credentials["password"])
mail.list()
mail.select('"[Gmail]/All Mail"')

if my_credentials["state"] == "zoomed":
    app.state("zoomed")
elif my_credentials["state"] == "fullscreen":
    app.geometry("1920x1080+-10+-10")

start_updater()
app.mainloop()
