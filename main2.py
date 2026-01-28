import tkinter as tk



class LoginApp:

    def __init__(self, root):
        self.root = root
        self.is_dark_mode = False
        

        self.light_mode = {
            'bg': 'white',
            'fg': 'black',
            'entry_bg': '#eee',
            'entry_fg': 'white',
            'btn_bg': '#ddd',
            'btn_fg': 'black'
        }

        self.dark_mode = {
            'bg': '#333',
            'fg': 'white',
            'entry_bg': '#555',
            'entry_fg': 'white',
            'btn_bg': '#444',
            'btn_fg': 'white'
        }




        self.label_username = tk.Label(root, text="Username:")
        self.label_username.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.entry_username = tk.Entry(root)
        self.entry_username.grid(row=0, column=1, padx=10, pady=10)

        self.label_password = tk.Label(root, text="Password:")
        self.label_password.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        self.entry_password = tk.Entry(root, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=10)

        self.button_login = tk.Button(root, text="Login", command=self.login)
        self.button_login.grid(row=2, column=0, columnspan=2, pady=10)

        self.toggle_button = tk.Button(root, text="Toggle Dark Mode", command=self.toggle_theme)
        self.toggle_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.apply_theme(self.light_mode)

       


    def apply_theme(self, theme):
        self.root.configure(bg=theme['bg'])
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=theme['bg'], fg=theme['fg'])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=theme['entry_bg'], fg=theme['entry_fg'], insertbackground=theme['fg'])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=theme['btn_bg'], fg=theme['btn_fg'])

    

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        if username == "admin" and password == "password":
           CustomeMessabox(
               self.root,
               title="login",
               message="Login Successful",
               theme=self.dark_mode if self.is_dark_mode else self.light_mode,
           )
        else:
            CustomeMessabox(
                self.root,
                title="login",
                message="Login Failed",
                theme=self.dark_mode if self.is_dark_mode else self.light_mode,
            )



    def toggle_theme(self):
        if self.is_dark_mode:
            self.apply_theme(self.light_mode)
        else:
            self.apply_theme(self.dark_mode)
        self.is_dark_mode = not self.is_dark_mode


class CustomeMessabox(tk.Toplevel):
    def __init__(self, parent, title, message,theme):
            super().__init__(parent)
            self.theme = theme
            
            self.title(title)
            self.geometry("300x150")
            self.configure(bg=self.theme['bg'])
            
            self.label = tk.Label(self, text=message, bg=self.theme['bg'], fg=self.theme['fg'])
            self.label.pack(pady=20, padx=20 )

            self.button_ok = tk.Button(self, text="OK", command=self.destroy,bg=self.theme['btn_bg'], fg=self.theme['btn_fg'])
            self.button_ok.pack(pady=10)




root = tk.Tk()
root.title("Login")
app = LoginApp(root)        
root.mainloop()
