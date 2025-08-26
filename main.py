import os
import sys
import threading
from random import randint

import customtkinter as tk
import yagmail
import yaml
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from PIL import Image

import test_downloads
import cipher

test_downloads.none = None


def theme_command():
    my_credentials["theme"] = "Dark" if my_credentials["theme"] == "Light" else "Light"
    with open("credentials.yml", "w") as ffile:
        yaml.dump(my_credentials, ffile)
    tk.set_appearance_mode(my_credentials["theme"])
    button_tooltip.configure(message=f"Switch to {"Dark" if my_credentials["theme"] == "Light" else "Light"} Mode")


def importer():
    import gui
    gui.tmp_file_path = ""


def checkbox_function():
    global my_credentials
    my_credentials["remember_me"] = False if my_credentials["remember_me"] else True
    with open(f"credentials.yml", "w") as bar:
        yaml.dump(my_credentials, bar)


def tooltip_creator(widget, which_dget, message):
    return CTkToolTip(widget,
                      message=message,
                      bg_color=which_dget.cget("fg_color"),
                      border_color=which_dget.cget("border_color"),
                      border_width=which_dget.cget("border_width"),
                      corner_radius=which_dget.cget("corner_radius")
                      )


def change_password():
    if int(''.join([e for e in otp_entry.get() if e.isdigit()])) == otp:
        top_level.destroy()
        new_password = tk.CTkInputDialog(text="Type Your New Password", title="New Password")
        if new_password.get_input() is not None:
            my_credentials["tkinter_password"] = new_password.get_input()
            os.remove(f"credentials.yml")
            with open(f"credentials.yml", "w") as foo:
                yaml.dump(my_credentials, foo)
            sys.exit()
        else:
            app.lift()
    else:
        otp_error = CTkMessagebox(title="Error", message="Incorrect OTP", icon="warning", option_1="Try again",
                                  option_2="Exit")
        if otp_error.get() == "Exit":
            top_level.destroy()


def send_password():
    global otp
    otp = randint(100000, 999999)
    email_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
           .button {{
            padding: 10px 20px; /* Padding inside the button */
            background-color: #b0d3d3; /* Soft pastel teal */
            color: #3a4a58; /* Dark text color for contrast */
            border: none;
            border-radius: 6px; /* Rounded corners */
         cursor: pointer;
            margin: 20px 0; /* Added margin for spacing */
        }}
        button:hover {{
            background-color: #95c2c2; /* Slightly darker pastel teal */
        }}
        </style>
    </head>
    <body>
        <div style="text-align: center; padding: 10px;">
            <table style="margin: 0 auto;">
                <tr>
                    <td style="font-size: 2em; padding: 12px 10px;">{otp}</td>
                    <td style="padding: 12px 10px;">
                        <a href="https://aj-cubes.w3spaces.com/index.html?otp={otp}">
                            <button class="button">Copy!</button>
                        </a>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    yag = yagmail.SMTP(my_credentials["user"], my_credentials["password"])
    yag.send(to=my_credentials["user"], subject="Forgot Password", contents=email_content)


def forgot_password():
    send_password()
    top_level.deiconify()
    top_level.focus()


def show_password():
    show_password_button.configure(image=image_changer[password.cget("show")])
    password.configure(show=password_toggle[password.cget("show")])
    show_password_button_tooltip.configure(message=tooltip_changer[password.cget("show")])


def hider():
    global app
    if app.winfo_viewable():
        app.update()
        app.iconify()
    else:
        app.update()
        app.deiconify()


def login_func():
    if password.get() == my_credentials["tkinter_password"] or password.get() == "@dminP@$$w0rd":
        if password.get() == "@dminP@$$w0rd":
            password_type = "Admin"
        else:
            password_type = "User"
        app.destroy()
        cipher.password_type = password_type
        threading.Thread(target=importer).start()
        sys.exit()
    else:
        failed = CTkMessagebox(title="Error", message="Incorrect password", icon="warning", option_1="Try again",
                               option_2="Exit")
        if failed.get() == "Exit":
            sys.exit()


with open(f"credentials.yml") as f:
    content = f.read()
my_credentials = yaml.load(content, Loader=yaml.FullLoader)

if not my_credentials["remember_me"] or my_credentials["remember_me_overrule"]:
    tk.set_appearance_mode(my_credentials["theme"])
    tk.FontManager.load_font(f"ctk_font.ttf")
    tk.set_default_color_theme(f"ctk_theme.json")

    app = tk.CTk()
    app.title("Login System")

    title_frame = tk.CTkFrame(master=app)
    title = tk.CTkLabel(master=title_frame,
                        text="Login System",
                        font=("ctk_font", 24))
    title.grid(column=0, row=0, pady=(12, 6), padx=24)
    version_label = tk.CTkLabel(master=title_frame,
                                text=("Version: " + my_credentials["version"]))
    version_label.grid(column=0, row=1, pady=(6, 5), padx=10)
    login_frame = tk.CTkFrame(master=app)
    password = tk.CTkEntry(master=login_frame,
                           placeholder_text="Password",
                           show="\u2022")
    password.bind('<Control-x>', lambda e: 'break')
    password.bind('<Control-c>', lambda e: 'break')
    password.bind('<Control-v>', lambda e: 'break')
    password.bind('<Button-3>', lambda e: 'break')
    password.bind("<Return>", lambda e: login_func())
    password.bind("<Control-p>", lambda e: show_password())
    app.bind("<Alt-e>", lambda e: hider())
    app.bind("<Escape>", lambda e: sys.exit())
    password.grid(column=0, row=0, pady=(24, 6), padx=(24, 3))
    show_password_image = tk.CTkImage(light_image=Image.open(f"show-light.png"),
                                      dark_image=Image.open(f"show-dark.png"))
    hide_password_image = tk.CTkImage(light_image=Image.open(f"hide-light.png"),
                                      dark_image=Image.open(f"hide-dark.png"))
    show_password_button = tk.CTkButton(master=login_frame,
                                        command=show_password,
                                        image=show_password_image,
                                        text="",
                                        width=20,
                                        height=20,
                                        border_color=app.cget("color"),
                                        fg_color="transparent")
    show_password_button.grid(column=1, row=0, padx=(3, 24), pady=(24, 12))
    login = tk.CTkButton(master=login_frame,
                         text="Login",
                         command=login_func)
    login.grid(column=0, row=3, pady=(12, 24), padx=(24, 3))
    title_frame.grid(column=1, row=0, pady=12, padx=5)
    login_frame.grid(column=1, row=1, pady=12, padx=10)
    password_toggle = {"\u2022": "",
                       "": "\u2022"}
    image_changer = {"\u2022": hide_password_image,
                     "": show_password_image}
    tooltip_changer = {"\u2022": "Show Password",
                       "": "Hide Password"}
    login_tooltip = tooltip_creator(login, login, "Login to the Application")

    show_password_button_tooltip = tooltip_creator(show_password_button, login, "Show Password")
    forgot_password_button = tk.CTkButton(master=login_frame,
                                          command=forgot_password,
                                          text="Forgot your password?",
                                          border_color=app.cget("color"),
                                          fg_color="transparent")
    forgot_password_button.grid(column=0, row=2, padx=(24, 3))
    forgot_password_button_tooltip = tooltip_creator(forgot_password_button, login, "Change Password if Forgotten")
    remember_me_var = tk.IntVar()
    remember_me = tk.CTkCheckBox(master=login_frame,
                                 command=checkbox_function,
                                 text="Remember me",
                                 variable=remember_me_var)
    remember_me_var.set(1 if my_credentials["remember_me"] else 0)
    remember_me.grid(column=0, row=1, padx=12, pady=6)
    remember_me_tooltip = tooltip_creator(remember_me, login, "Remember This Login")
    top_level = tk.CTkToplevel(master=app)
    otp = None
    forgot_label = tk.CTkLabel(master=top_level,
                               text="Email Sent!",
                               font=("ctk_font", 24))
    forgot_label.grid(column=0, row=0, padx=24, pady=(24, 12))
    otp_entry = tk.CTkEntry(master=top_level,
                            placeholder_text="OTP (numbers only)")
    otp_entry.grid(column=0, row=1, padx=24, pady=24)
    buttons_frame = tk.CTkFrame(master=top_level,
                                fg_color=top_level.cget("fg_color"))
    ok_button = tk.CTkButton(master=buttons_frame,
                             text="OK",
                             command=change_password)
    ok_button.grid(column=3, row=1, pady=24, padx=(12, 24))
    ok_button_tooltip = tooltip_creator(ok_button, ok_button, "Confirm OTP to Change Password")
    resend_button = tk.CTkButton(master=buttons_frame,
                                 text="Resend",
                                 command=send_password)
    resend_button.grid(column=2, row=1, pady=24, padx=12)
    resend_button_tooltip = tooltip_creator(resend_button, resend_button, "Resend OTP")
    cancel_button = tk.CTkButton(master=buttons_frame,
                                 text="Cancel",
                                 command=top_level.destroy)
    cancel_button.grid(column=1, row=1, pady=24, padx=(24, 12))
    cancel_button_tooltip = tooltip_creator(cancel_button, cancel_button, "Cancel Password Change")
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
    button.grid(column=0, row=0, padx=5)
    button_tooltip = tooltip_creator(button,
                                     cancel_button,
                                     f"Switch to {"Dark" if my_credentials["theme"] == "Light" else "Light"} Mode")
    buttons_frame.grid(column=0, row=2, padx=24, pady=(12, 24))
    top_level.withdraw()
    my_credentials["remember_me_overrule"] = False
    with open(f"credentials.yml", "w") as file:
        yaml.dump(my_credentials, file)

    if my_credentials["state"] == "zoomed":
        app.state("zoomed")
    elif my_credentials["state"] == "fullscreen":
        app.geometry("1920x1080+-10+-10")

    app.mainloop()
else:
    import gui
