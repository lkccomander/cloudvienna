import tkinter as tk
from tkinter import messagebox, ttk

from api_client import (
    ApiError,
    create_api_user,
    list_api_users,
    reset_api_user_password,
    update_api_user,
)
from i18n import t


ROLE_OPTIONS = ("admin", "coach", "receptionist")


def build(tab_users):
    us_username = tk.StringVar()
    us_role = tk.StringVar(value="coach")
    us_password = tk.StringVar()

    selected_user_id = None
    selected_user_active = None

    users_form = ttk.LabelFrame(tab_users, text=t("label.user_form"), padding=10)
    users_form.grid(row=1, column=0, sticky="nw", padx=10)

    users_list = ttk.LabelFrame(tab_users, text=t("label.users_list"), padding=10)
    users_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    tab_users.grid_rowconfigure(2, weight=1)
    tab_users.grid_columnconfigure(0, weight=1)

    ttk.Label(users_form, text=t("label.username")).grid(row=0, column=0, sticky="w")
    ttk.Entry(users_form, textvariable=us_username, width=30).grid(row=0, column=1, sticky="w")

    ttk.Label(users_form, text=t("label.role")).grid(row=1, column=0, sticky="w")
    ttk.Combobox(
        users_form,
        textvariable=us_role,
        values=ROLE_OPTIONS,
        state="readonly",
        width=27,
    ).grid(row=1, column=1, sticky="w")

    ttk.Label(users_form, text=t("label.password")).grid(row=2, column=0, sticky="w")
    ttk.Entry(users_form, textvariable=us_password, width=30, show="*").grid(row=2, column=1, sticky="w")

    btns = ttk.Frame(users_form)
    btns.grid(row=3, column=0, columnspan=2, pady=10, sticky="w")

    us_btn_add = ttk.Button(btns, text=t("button.register"))
    us_btn_update = ttk.Button(btns, text=t("button.update"))
    us_btn_reset_pwd = ttk.Button(btns, text=t("button.reset_password"))
    us_btn_deactivate = ttk.Button(btns, text=t("button.deactivate"))
    us_btn_reactivate = ttk.Button(btns, text=t("button.reactivate"))
    us_btn_refresh = ttk.Button(btns, text=t("button.refresh"))

    us_btn_add.grid(row=0, column=0, padx=4)
    us_btn_update.grid(row=0, column=1, padx=4)
    us_btn_reset_pwd.grid(row=0, column=2, padx=4)
    us_btn_deactivate.grid(row=0, column=3, padx=4)
    us_btn_reactivate.grid(row=0, column=4, padx=4)
    us_btn_refresh.grid(row=0, column=5, padx=4)

    users_tree = ttk.Treeview(
        users_list,
        columns=("id", "username", "role", "status", "created_at"),
        show="headings",
    )
    users_tree.heading("id", text=t("label.id"))
    users_tree.heading("username", text=t("label.username"))
    users_tree.heading("role", text=t("label.role"))
    users_tree.heading("status", text=t("label.status"))
    users_tree.heading("created_at", text=t("label.created_at"))

    users_tree.column("id", width=80, anchor="center")
    users_tree.column("username", width=260)
    users_tree.column("role", width=140, anchor="center")
    users_tree.column("status", width=140, anchor="center")
    users_tree.column("created_at", width=220)

    users_tree.tag_configure("active", foreground="green")
    users_tree.tag_configure("inactive", foreground="red")

    users_tree.pack(fill=tk.BOTH, expand=True)
    x_scroll = ttk.Scrollbar(users_list, orient="horizontal", command=users_tree.xview)
    users_tree.configure(xscrollcommand=x_scroll.set)
    x_scroll.pack(fill=tk.X)

    def _set_button_states():
        if selected_user_id is None:
            us_btn_update.config(state="disabled")
            us_btn_reset_pwd.config(state="disabled")
            us_btn_deactivate.config(state="disabled")
            us_btn_reactivate.config(state="disabled")
            return
        us_btn_update.config(state="normal")
        us_btn_reset_pwd.config(state="normal")
        if selected_user_active:
            us_btn_deactivate.config(state="normal")
            us_btn_reactivate.config(state="disabled")
        else:
            us_btn_deactivate.config(state="disabled")
            us_btn_reactivate.config(state="normal")

    def _validate_role(role_value):
        return role_value in ROLE_OPTIONS

    def _clear_form():
        nonlocal selected_user_id, selected_user_active
        selected_user_id = None
        selected_user_active = None
        us_username.set("")
        us_role.set("coach")
        us_password.set("")
        users_tree.selection_remove(*users_tree.selection())
        _set_button_states()

    def load_users():
        users_tree.delete(*users_tree.get_children())
        try:
            rows = list_api_users()
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))
            rows = []

        if not rows:
            users_tree.insert("", tk.END, values=("", t("label.no_data"), "", "", ""), tags=("inactive",))
            _clear_form()
            return

        for row in rows:
            is_active = bool(row.get("active"))
            users_tree.insert(
                "",
                tk.END,
                values=(
                    row.get("id"),
                    row.get("username"),
                    row.get("role"),
                    t("label.active") if is_active else t("label.inactive"),
                    row.get("created_at"),
                ),
                tags=("active" if is_active else "inactive",),
            )
        _clear_form()

    def on_select(_event):
        nonlocal selected_user_id, selected_user_active
        selected = users_tree.selection()
        if not selected:
            return
        values = users_tree.item(selected[0]).get("values", [])
        if not values or not values[0]:
            _clear_form()
            return
        selected_user_id = int(values[0])
        us_username.set(values[1] or "")
        selected_role = values[2] if values[2] in ROLE_OPTIONS else "coach"
        us_role.set(selected_role)
        us_password.set("")
        selected_user_active = users_tree.item(selected[0]).get("tags", ("inactive",))[0] == "active"
        _set_button_states()

    def register_user():
        username = us_username.get().strip()
        role = us_role.get().strip()
        password = us_password.get()

        if len(username) < 3:
            messagebox.showerror(t("alert.validation_title"), t("alert.username_min"))
            return
        if len(password) < 10:
            messagebox.showerror(t("alert.validation_title"), t("alert.password_min"))
            return
        if not _validate_role(role):
            messagebox.showerror(t("alert.validation_title"), t("alert.invalid_role"))
            return
        try:
            create_api_user({"username": username, "password": password, "role": role})
            load_users()
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))

    def update_user():
        if selected_user_id is None:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_user"))
            return
        username = us_username.get().strip()
        role = us_role.get().strip()
        password = us_password.get()
        if len(username) < 3:
            messagebox.showerror(t("alert.validation_title"), t("alert.username_min"))
            return
        if not _validate_role(role):
            messagebox.showerror(t("alert.validation_title"), t("alert.invalid_role"))
            return
        if password and len(password) < 10:
            messagebox.showerror(t("alert.validation_title"), t("alert.password_min"))
            return
        payload = {"username": username, "role": role}
        if password:
            payload["new_password"] = password
        try:
            update_api_user(selected_user_id, payload)
            us_password.set("")
            load_users()
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))

    def reset_password():
        if selected_user_id is None:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_user"))
            return
        password = us_password.get()
        if len(password) < 10:
            messagebox.showerror(t("alert.validation_title"), t("alert.password_min"))
            return
        try:
            reset_api_user_password(selected_user_id, password)
            us_password.set("")
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))

    def deactivate_user():
        if selected_user_id is None:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_user"))
            return
        try:
            update_api_user(selected_user_id, {"active": False})
            load_users()
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))

    def reactivate_user():
        if selected_user_id is None:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_user"))
            return
        try:
            update_api_user(selected_user_id, {"active": True})
            load_users()
        except ApiError as exc:
            messagebox.showerror(t("alert.api_error_title"), str(exc))

    users_tree.bind("<<TreeviewSelect>>", on_select)
    us_btn_add.config(command=register_user)
    us_btn_update.config(command=update_user)
    us_btn_reset_pwd.config(command=reset_password)
    us_btn_deactivate.config(command=deactivate_user)
    us_btn_reactivate.config(command=reactivate_user)
    us_btn_refresh.config(command=load_users)

    _set_button_states()

    return {"load_users": load_users}
