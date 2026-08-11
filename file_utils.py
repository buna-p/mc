import tkinter as tk
from tkinter import filedialog, messagebox


def _root():
    root = tk.Tk()
    root.withdraw()
    return root


def select_input_file(title: str = 'Выберите файл с данными') -> str:
    root = _root()
    file_path = filedialog.askopenfilename(title=title, filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")])
    root.destroy()
    return file_path 


def select_output_catalog(title: str = 'Сохранить как') -> str:
    root = _root()
    path = filedialog.asksaveasfilename(title=title,
                                        defaultextension=".xlsx",
                                        filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")],
                                        initialfile="Результат.xlsx",)
    root.destroy()
    return path


def error(msg: str):
    root = _root()
    messagebox.showerror('Ошибка', msg)
    root.destroy()


def info(msg: str):
    root = _root()
    messagebox.showinfo('Информация', msg)
    root.destroy()