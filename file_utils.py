import tkinter as tk
from tkinter import filedialog, messagebox


def _root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def select_input_file(title: str = 'Выберите файл с данными') -> str:
    root = _root()
    try:
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")])
    finally:
        root.destroy()
    return file_path 


def select_output_catalog(title: str = 'Сохранить как') -> str:
    root = _root()
    try:
        path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")],
            initialfile="Результат.xlsx",)
    finally:
        root.destroy()
    return path


def select_payer_file(title: str = 'Выберите файл со справочником Payer BAN') -> str:
    root = _root()
    try:
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")])
    finally:
        root.destroy()
    return file_path 


def error(msg: str):
    root = _root()
    messagebox.showerror('Ошибка', msg)
    root.destroy()


def info(msg: str):
    root = _root()
    messagebox.showinfo('Информация', msg)
    root.destroy()