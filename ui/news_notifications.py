import tkinter as tk
from tkinter import ttk

from db import execute
from i18n import t


def build(tab_news):
    header = ttk.Frame(tab_news)
    header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

    ttk.Label(header, text=t("label.birthdays_this_month")).grid(row=0, column=0, sticky="w")

    count_var = tk.StringVar(value=t("label.results", count=0))
    ttk.Label(header, textvariable=count_var).grid(row=0, column=1, sticky="w", padx=(10, 0))

    tree_frame = ttk.LabelFrame(tab_news, text=t("label.birthdays_list"), padding=10)
    tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    tab_news.grid_rowconfigure(1, weight=1)
    tab_news.grid_columnconfigure(0, weight=1)

    birthdays_tree = ttk.Treeview(
        tree_frame,
        columns=("name", "belt", "birthday"),
        show="headings"
    )

    header_map = {
        "name": "label.name",
        "belt": "label.belt",
        "birthday": "label.birthday",
    }
    for c in birthdays_tree["columns"]:
        birthdays_tree.heading(c, text=t(header_map.get(c, c)))

    birthdays_tree.tag_configure("active", foreground="green")
    birthdays_tree.tag_configure("inactive", foreground="red")

    birthdays_tree.pack(fill=tk.BOTH, expand=True)

    x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=birthdays_tree.xview)
    birthdays_tree.configure(xscrollcommand=x_scroll.set)
    x_scroll.pack(fill=tk.X)

    def load_birthdays():
        for r in birthdays_tree.get_children():
            birthdays_tree.delete(r)

        rows = execute("""
            SELECT name, belt, birthday, active
            FROM t_students
            WHERE birthday IS NOT NULL
              AND EXTRACT(MONTH FROM birthday) = EXTRACT(MONTH FROM CURRENT_DATE)
            ORDER BY EXTRACT(DAY FROM birthday), name
        """)

        if not rows:
            birthdays_tree.insert(
                "",
                tk.END,
                values=(t("label.no_data"), "", ""),
            )
            count_var.set(t("label.results", count=0))
            return

        for name, belt, birthday, active in rows:
            tag = "active" if active else "inactive"
            birthdays_tree.insert(
                "",
                tk.END,
                values=(name, belt, str(birthday)),
                tags=(tag,)
            )

        count_var.set(t("label.results", count=len(rows)))

    ttk.Button(header, text=t("button.refresh"), command=load_birthdays).grid(
        row=0, column=2, sticky="e", padx=(10, 0)
    )
    header.grid_columnconfigure(2, weight=1)

    load_birthdays()

    return {
        "load_birthdays": load_birthdays,
    }
