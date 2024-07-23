import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64
import json
import datetime
import os
import io
import threading
import re
import platform
import subprocess
import string
from PIL import Image, ImageTk
import pickle
import tempfile
import shutil
import time

class CenteredDialog:
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

class FileConflictDialog(tk.Toplevel, CenteredDialog):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.filename = filename
        self.result = None
        self.apply_to_all = tk.BooleanVar(value=False)
        self.title("File Already Exists")
        self.geometry("400x200")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.attributes('-topmost', True)
        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        message = f"The file '{self.filename}' already exists in the destination.\nWhat would you like to do?"
        ttk.Label(self, text=message, wraplength=380).pack(pady=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        for text, result in [("Replace the file in the destination", "replace"),
                             ("Keep both files", "keep_both"),
                             ("Skip this file", "skip")]:
            ttk.Button(button_frame, text=text, 
                       command=lambda r=result: self.set_result(r)).pack(fill='x')

        ttk.Checkbutton(self, text="Apply this action to all conflicts", 
                        variable=self.apply_to_all).pack(pady=5)

    def set_result(self, result):
        self.result = result
        self.destroy()

    def on_close(self):
        self.result = "cancel"
        self.destroy()

class CustomDialog(tk.Toplevel, CenteredDialog):
    def __init__(self, parent, title, prompt, initial_value=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.result = None

        ttk.Label(self, text=prompt).pack(pady=10)
        self.entry = ttk.Entry(self, width=40)
        self.entry.insert(0, initial_value)
        self.entry.pack(pady=10)
        self.entry.focus_set()

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        self.bind("<Return>", self.on_ok)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.center_window()

    def on_ok(self, event=None):
        self.result = self.entry.get()
        self.destroy()

class CustomIntegerDialog(tk.Toplevel, CenteredDialog):
    def __init__(self, parent, title, prompt, initial_value=1, min_value=1, max_value=1000):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.result = None

        ttk.Label(self, text=prompt).pack(pady=10)
        self.entry = ttk.Entry(self, width=10)
        self.entry.insert(0, str(initial_value))
        self.entry.pack(pady=10)
        self.entry.focus_set()

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)

        self.min_value = min_value
        self.max_value = max_value

        self.bind("<Return>", self.on_ok)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.center_window()

    def on_ok(self, event=None):
        try:
            value = int(self.entry.get())
            if self.min_value <= value <= self.max_value:
                self.result = value
                self.destroy()
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", f"Please enter a valid integer between {self.min_value} and {self.max_value}.")

class GifPreviewWindow(tk.Toplevel):
    def __init__(self, master, gif_path):
        super().__init__(master)
        self.title("GIF Preview")
        self.gif_path = gif_path
        self.result = None
        self.gif = None  # GIF dosyasını tutacak değişken

        self.load_gif()
        self.create_widgets()
        self.center_window()

    def load_gif(self):
        self.gif = Image.open(self.gif_path)
        self.frames = []
        try:
            while True:
                self.frames.append(ImageTk.PhotoImage(self.gif.copy()))
                self.gif.seek(len(self.frames))
        except EOFError:
            pass

    def create_widgets(self):
        # GIF'in boyutlarını al
        width, height = self.gif.size
        
        # Ekran boyutlarını al
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Maksimum pencere boyutunu belirle (ekranın %80'i)
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # Eğer GIF boyutu maksimum boyuttan büyükse, oranı koru ve küçült
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            width = int(width * ratio)
            height = int(height * ratio)

        self.canvas = tk.Canvas(self, width=width, height=height)
        self.canvas.pack()

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.current_frame = 0
        self.show_frame()

    def show_frame(self):
        frame = self.frames[self.current_frame]
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, image=frame)
        
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after(self.gif.info.get('duration', 100), self.show_frame)  # Default to 100ms if duration not specified

    def save(self):
        self.result = True
        self.cleanup()
        self.destroy()

    def cancel(self):
        self.result = False
        self.cleanup()
        self.destroy()

    def cleanup(self):
        # GIF dosyasını kapat
        if self.gif:
            self.gif.close()
        # Frames'i temizle
        self.frames.clear()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

class BaseConverter:
    def __init__(self, master):
        self.master = master
        self.files = []
        self.sort_order = True
        self.undo_stack = []
        self.conflict_resolution = None
        self.apply_to_all = False
        self.text_editors = {}
        self.current_session_file = None
        self.create_widgets()
        self.bind_shortcuts()
        self.file_counter = 0
        self.bind_events()  # Yeni metod

        self.changes_made = False

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.tree = ttk.Treeview(self.frame, columns=('Filename', 'Note'), show='headings', selectmode='extended')
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.grid(column=0, row=0, sticky=(tk.W, tk.E))
        
        self.create_buttons()

        self.tree = ttk.Treeview(self.frame, columns=('Filename', 'Note'), show='headings')
        self.tree.heading('Filename', text='File name')
        self.tree.heading('Note', text='Note')
        self.tree.column('Filename', width=400)
        self.tree.column('Note', width=200)
        self.tree.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(column=1, row=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<BackSpace>', self.remove_selected)
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        self.progress = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(column=0, row=2, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(column=0, row=3, sticky=(tk.W, tk.E))

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop)

    def bind_events(self):
        self.tree.bind('<Delete>', self.remove_selected)
        self.tree.bind('<Control-a>', self.select_all)
        self.master.bind('<Control-A>', self.select_all)  # Büyük harf için

    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return 'break'  # Varsayılan işlemi engelle
    
    def save_session(self):
        if self.current_session_file:
            save_path = self.current_session_file
        else:
            save_path = filedialog.asksaveasfilename(defaultextension=".jft", filetypes=[("JFT files", "*.jft")])
        
        if save_path:
            session_data = {
                'files': self.files,
                'sort_order': self.sort_order,
                'converter_type': self.__class__.__name__
            }
            with open(save_path, 'wb') as f:
                pickle.dump(session_data, f)
            self.current_session_file = save_path
            messagebox.showinfo("Başarılı", "Oturum başarıyla kaydedildi.")
            self.changes_made = False

    def load_session(self, filename):
        with open(filename, 'rb') as f:
            session_data = pickle.load(f)
        self.files = session_data['files']
        self.sort_order = session_data['sort_order']
        self.current_session_file = filename
        self.update_treeview()
        self.changes_made = False

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for item, path, filename, *rest in self.files:
            values = [filename] + rest
            new_item = self.tree.insert('', 'end', values=values)
            self.files[self.files.index((item, path, filename, *rest))] = (new_item, path, filename, *rest)
        self.sort_items()
        
    def create_buttons(self):
        raise NotImplementedError("Subclasses must implement create_buttons method")

    def bind_shortcuts(self):
        self.master.bind('<Control-z>', lambda event: self.undo_last_action())

    @staticmethod
    def natural_sort_key(s):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

    def sort_items(self):
        items = [(self.tree.set(k, 'Filename'), k) for k in self.tree.get_children('')]
        items.sort(key=lambda x: self.natural_sort_key(x[0]))  # Her zaman artan sıralama
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        
        self.files.sort(key=lambda x: self.natural_sort_key(x[2]))  # Dahili listeyi de sırala
    def drop(self, event):
        paths = self.tree.tk.splitlist(event.data)
        self.process_dropped_items(paths)

    def resolve_conflict(self, filename):
        if not self.apply_to_all:
            dialog = FileConflictDialog(self.master, filename)
            self.master.wait_window(dialog)
            self.conflict_resolution = dialog.result
            self.apply_to_all = dialog.apply_to_all.get()
        return self.conflict_resolution

    def add_file(self, path):
        # Bu metod alt sınıflarda override edilecek
        pass

    def process_dropped_items(self, paths):
        self.conflict_resolution = None
        self.apply_to_all = False
        
        sorted_paths = sorted(paths, key=lambda p: self.natural_sort_key(os.path.basename(p)))
        
        added_items = []
        for path in sorted_paths:
            if os.path.isdir(path):
                self.process_directory(path)
            else:
                item = self.add_file(path)
                if item:
                    added_items.append(item)
        
        if added_items:
            self.undo_stack.append(('add', [file for file in self.files if file[0] in added_items]))
        self.sort_items()

    def process_directory(self, directory):
        files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        sorted_files = sorted(files, key=lambda p: self.natural_sort_key(os.path.basename(p)))
        
        for file_path in sorted_files:
            self.add_file(file_path)

    def cleanup(self):
        self.master.unbind_all('<Control-z>')
        self.master.protocol("WM_DELETE_WINDOW", self.master.on_closing)
        self.frame.destroy()
        del self

    def back_to_main_menu(self):
        self.frame.destroy()
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.show_main_menu()

    def remove_selected(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        if len(selected_items) == 1:
            message = "Are you sure you want to remove this item?"
        else:
            message = f"Are you sure you want to remove these {len(selected_items)} items?"

        if messagebox.askyesno("Confirm Removal", message):
            removed_items = []
            for item in selected_items:
                values = self.tree.item(item, 'values')
                file_info = next((file for file in self.files if file[0] == item), None)
                if file_info:
                    removed_items.append(file_info)
                    self.tree.delete(item)
                    self.files.remove(file_info)

            if removed_items:
                self.undo_stack.append(('remove', removed_items))
                self.changes_made = True
                self.tree.update()

    def on_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.tree.selection_set(item)
        self.hide_text_editor()

    def on_select(self, event):
        self.hide_text_editor()

    def open_file(self, item):
        file_info = next((file for file in self.files if file[0] == item), None)
        if file_info:
            path = file_info[1]
            self.safe_open_file(path)

    @staticmethod
    def safe_open_file(path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", path])
            else:  # Linux and other systems
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def edit_note(self, item):
        self.hide_text_editor()
        current_value = self.tree.set(item, 'Note')
        
        text_editor = tk.Text(self.tree, wrap=tk.WORD, height=3)
        text_editor.insert(tk.END, current_value)
        
        def save_note(event=None):
            new_value = text_editor.get("1.0", tk.END).strip()
            if new_value != current_value:
                self.tree.set(item, 'Note', new_value)
                self.update_note_in_files(item, new_value)
                self.undo_stack.append(('edit_note', (item, current_value)))
                self.changes_made = True
            self.hide_text_editor()

        text_editor.bind("<FocusOut>", save_note)
        text_editor.bind("<Return>", save_note)
        
        bbox = self.tree.bbox(item, '#2')
        if bbox:
            text_editor.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        
        self.text_editors[item] = text_editor
        text_editor.focus_set()

    def update_note_in_files(self, item, new_value):
        for i, file_info in enumerate(self.files):
            if file_info[0] == item:
                self.files[i] = (*file_info[:-1], new_value)
                break

    def hide_text_editor(self):
        for editor in self.text_editors.values():
            editor.place_forget()
        self.text_editors.clear()

    def reverse_order(self):
        self.sort_order = not self.sort_order
        self.sort_items()

    def rename_all(self):
        if not self.files:
            messagebox.showerror("Error", "No files to rename.")
            return

        dialog = CustomDialog(self.master, "Rename All", "Enter new base name for files:")
        self.master.wait_window(dialog)
        new_base_name = dialog.result
        if new_base_name:
            old_names = []
            # Dosya adlarından sayıları çıkar ve sırala
            numbered_files = sorted([(int(''.join(filter(str.isdigit, os.path.splitext(file[2])[0]))), file) for file in self.files])
            
            for index, (_, file) in enumerate(numbered_files, start=1):
                item, old_path, old_filename, *rest = file
                old_names.append((item, old_filename))
                extension = os.path.splitext(old_filename)[1]
                new_name = f"{new_base_name}_{index}{extension}"
                new_path = os.path.join(os.path.dirname(old_path), new_name)

                try:
                    os.rename(old_path, new_path)
                    self.tree.item(item, values=(new_name, *rest))
                    self.files[self.files.index(file)] = (item, new_path, new_name, *rest)
                except OSError as e:
                    messagebox.showerror("Error", f"Failed to rename {old_path}: {str(e)}")

            self.undo_stack.append(('rename_all', old_names))
            messagebox.showinfo("Rename Complete", "All files have been renamed.")
            self.sort_items()
            self.changes_made = True
            
    def get_next_filename(self, filename):
        base, ext = os.path.splitext(filename)
        existing_files = [file[2] for file in self.files]
        
        if not existing_files:
            return f"{base}_1{ext}"
        
        existing_base = os.path.splitext(existing_files[0])[0].rsplit('_', 1)[0]
        numbers = [int(os.path.splitext(f)[0].rsplit('_', 1)[1]) for f in existing_files if f.startswith(existing_base)]
        if numbers:
            last_number = max(numbers)
        else:
            last_number = 0
        
        if base == existing_base:
            return f"{base}_{last_number + 1}{ext}"
        else:
            return f"{existing_base}_{last_number + 1}{ext}"

    @staticmethod
    def sanitize_filename(filename):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        sanitized = ''.join(c for c in filename if c in valid_chars)
        sanitized = sanitized.strip()
        sanitized = sanitized.lstrip('.')
        if not sanitized:
            return "unnamed_file"
        return sanitized

    def back_to_main_menu_with_save_prompt(self):
        if self.changes_made:
            response = messagebox.askyesnocancel("Save the changes", "Do you want to save the changes?")
            if response is None:  # İptal edildi
                return
            elif response:  # Evet
                self.save_session()
        
        self.cleanup()
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.is_converter_open = False
        self.master.show_main_menu()

    def undo_last_action(self):
        if not self.undo_stack:
            return

        action, items = self.undo_stack.pop()
        
        try:
            if action == 'remove':
                for item, path, filename, *rest in items:
                    new_item = self.tree.insert('', 'end', values=(filename, *rest))
                    self.files.append((new_item, path, filename, *rest))
            elif action == 'add':
                for item, _, _, *_ in items:
                    if self.tree.exists(item):
                        self.tree.delete(item)
                        self.files = [file for file in self.files if file[0] != item]
            elif action == 'rename_all':
                for item, old_name in items:
                    if self.tree.exists(item):
                        current_values = self.tree.item(item, 'values')
                        file_info = next((file for file in self.files if file[0] == item), None)
                        if file_info:
                            new_path = os.path.join(os.path.dirname(file_info[1]), old_name)
                            try:
                                os.rename(file_info[1], new_path)
                                self.tree.item(item, values=(old_name, *current_values[1:]))
                                index = self.files.index(file_info)
                                self.files[index] = (item, new_path, old_name, *file_info[3:])
                            except OSError as e:
                                messagebox.showerror("Error", f"Failed to rename file: {str(e)}")
            elif action == 'edit_note':
                item, old_value = items
                if self.tree.exists(item):
                    current_values = self.tree.item(item, 'values')
                    self.tree.item(item, values=(*current_values[:-1], old_value))
                    file_info = next((file for file in self.files if file[0] == item), None)
                    if file_info:
                        index = self.files.index(file_info)
                        self.files[index] = (*file_info[:-1], old_value)
            elif action == 'edit_repeat':
                item, old_value = items
                if self.tree.exists(item):
                    current_values = self.tree.item(item, 'values')
                    self.tree.item(item, values=(current_values[0], old_value, *current_values[2:]))
                    file_info = next((file for file in self.files if file[0] == item), None)
                    if file_info:
                        index = self.files.index(file_info)
                        self.files[index] = (*file_info[:3], old_value, *file_info[4:])
            elif action == 'set_all_repeats':
                for item, old_value in items:
                    if self.tree.exists(item):
                        self.tree.set(item, 'Repeat', old_value)
                        file_info = next((file for file in self.files if file[0] == item), None)
                        if file_info:
                            index = self.files.index(file_info)
                            self.files[index] = (*file_info[:3], old_value, *file_info[4:])
            
            self.sort_items()
            self.changes_made = True
        except Exception as e:
            messagebox.showerror("Undo Error", f"An error occurred during undo: {str(e)}")
            print(f"Undo error: {str(e)}")
        finally:
            self.tree.update()

    def tree_exists(self, item):
        try:
            self.tree.item(item)
            return True
        except tk.TclError:
            return False

    def find_insert_index(self, filename):
        for index, child in enumerate(self.tree.get_children()):
            if self.natural_sort_key(filename) < self.natural_sort_key(self.tree.item(child)['values'][0]):
                return index
        return 'end'

    def on_closing(self):
        if self.changes_made:
            response = messagebox.askyesnocancel("Save Session", "Do you want to save the current session?")
            if response is None:  # İptal edildi
                return
            elif response:  # Evet
                self.save_session()
        
        self.cleanup()
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.is_converter_open = False
        self.master.destroy()

    def safe_remove(self, path):
        max_attempts = 5
        attempts = 0
        while attempts < max_attempts:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Successfully removed {path}")
                    return
            except Exception as e:
                print(f"Error removing file {path} (attempt {attempts + 1}): {e}")
                attempts += 1
                time.sleep(0.1)  # Kısa bir süre bekle ve tekrar dene
    
        if os.path.exists(path):
            print(f"Failed to remove {path} after {max_attempts} attempts")

    def update_progress(self, value, status):
        self.progress['value'] = value
        self.status_label['text'] = status
        self.master.update_idletasks()

class ImageConverter(BaseConverter):
    def __init__(self, master):
        super().__init__(master)
        self.tree.configure(columns=('Filename', 'Repeat', 'Note'))
        self.tree.heading('Filename', text='File name')
        self.tree.heading('Repeat', text='Repeat Count')
        self.tree.heading('Note', text='Note')
        self.tree.column('Filename', width=300)
        self.tree.column('Repeat', width=100)
        self.tree.column('Note', width=200)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.frame_counter = {}  # Her benzersiz görüntü için sayaç
        self.tree.bind('<Double-1>', self.on_double_click)

    def create_buttons(self):
        buttons = [
            ("Add Images", self.add_images),
            ("Remove", self.remove_selected),
            ("Set Repeats", self.set_all_repeats),
            ("JSON", self.convert_to_json),
            ("GIF", self.convert_to_gif),
            ("Reverse", self.reverse_order),
            ("Rename All", self.rename_all),
            ("Undo", self.undo_last_action),
            ("Save", self.save_session),
            ("Load", self.load_session_dialog),
            ("Menu", self.back_to_main_menu_with_save_prompt)
        ]
    
        for i, (text, command) in enumerate(buttons):
            self.button_frame.grid_columnconfigure(i, weight=1)
            ttk.Button(self.button_frame, text=text, command=command).grid(column=i, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)

    def load_session_dialog(self):
        filename = filedialog.askopenfilename(filetypes=[("JFT files", "*.jft")])
        if filename:
            self.load_session(filename)

    def add_file(self, path):
        if self.is_valid_image(path):
            self.file_counter += 1
            original_filename = os.path.basename(path)
            new_filename = f"work_{self.file_counter}{os.path.splitext(original_filename)[1]}"
            
            # Yeni bir giriş oluştur
            item = self.tree.insert('', 'end', values=(new_filename, '1', ''))
            self.files.append((item, path, new_filename, 1, ''))
            self.undo_stack.append(('add', [(item, path, new_filename, 1, '')]))
            self.changes_made = True
            
            self.tree.update()
            return item
        else:
            messagebox.showwarning("Invalid Image", f"The file {path} is not a valid image and will be skipped.")
            return None

    def get_next_filename(self, filename):
        name, ext = os.path.splitext(filename)
        counter = 1
        new_filename = f"{name}_{counter}{ext}"
        while any(file[2] == new_filename for file in self.files):
            counter += 1
            new_filename = f"{name}_{counter}{ext}"
        return new_filename
    
    def is_valid_file(self, path):
        return self.is_valid_image(path)

    @staticmethod
    def is_valid_image(path):
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def on_double_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            column = self.tree.identify_column(event.x)
            if column == '#1':  # Filename column
                self.open_file(item)
            elif column == '#2':  # Repeat Count column
                self.edit_repeat_count(item)
            elif column == '#3':  # Note column
                self.edit_note(item)

    def add_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        added_items = []
        for path in file_paths:
            item = self.add_file(path)
            if item:
                added_items.append(item)
        if added_items:
            self.undo_stack.append(('add', added_items))
        self.sort_items()

    def edit_repeat_count(self, item):
        current_value = int(self.tree.set(item, 'Repeat'))
        dialog = CustomIntegerDialog(self.master, "Edit Repeat Count", 
                                     "Enter new repeat count:", 
                                     initial_value=current_value, 
                                     min_value=1, max_value=1000)
        self.master.wait_window(dialog)
        new_value = dialog.result
        if new_value is not None and new_value != current_value:
            self.tree.set(item, 'Repeat', new_value)
            for i, (tree_item, path, filename, _, note) in enumerate(self.files):
                if tree_item == item:
                    self.files[i] = (tree_item, path, filename, new_value, note)
                    self.undo_stack.append(('edit_repeat', (item, current_value)))
                    break
            self.changes_made = True

    def set_all_repeats(self):
        dialog = CustomDialog(self.master, "Set All Repeats", "Enter repeat count for all images:", "")
        self.master.wait_window(dialog)
        if dialog.result:
            try:
                repeat_value = int(dialog.result)
                if 1 <= repeat_value <= 1000:
                    old_values = []
                    for item in self.tree.get_children():
                        old_values.append((item, self.tree.set(item, 'Repeat')))
                        self.tree.set(item, 'Repeat', repeat_value)
                    self.files = [(item, path, filename, repeat_value, note) for item, path, filename, _, note in self.files]
                    self.undo_stack.append(('set_all_repeats', old_values))
                    self.changes_made = True
                else:
                    raise ValueError
            except ValueError:
                tk.messagebox.showerror("Invalid Input", "Please enter a valid integer between 1 and 1000.")

    def convert_to_json(self):
        if not self.files:
            messagebox.showerror("Error", "Please add images first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not save_path:
            return

        threading.Thread(target=self._process_images_to_json, args=(save_path,)).start()

    def _process_images_to_json(self, save_path):
        try:
            total_images = sum(repeat for _, _, _, repeat, _ in self.files)
            processed_images = 0
            self.frame_counter.clear()

            self.update_progress(0, "Starting conversion to JSON...")

            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_file.write('[')
                first_item = True
                for _, path, filename, repeat, _ in self.files:
                    base_name = os.path.splitext(filename)[0]
                    if base_name not in self.frame_counter:
                        self.frame_counter[base_name] = 0
                    
                    for i in range(repeat):
                        self.frame_counter[base_name] += 1
                        image_json = self._image_to_json(path, base_name, self.frame_counter[base_name])
                        if image_json:
                            if not first_item:
                                temp_file.write(',')
                            json.dump(image_json, temp_file)
                            first_item = False
                            processed_images += 1
                            self.update_progress((processed_images / total_images) * 100,
                                                 f"Processing image {processed_images} of {total_images}")
                temp_file.write(']')

            self.update_progress(100, "Saving JSON file...")

            os.replace(temp_file.name, save_path)
            
            self.update_progress(100, "Conversion complete!")
            self.master.after(0, lambda: messagebox.showinfo("Success", f"JSON file saved as {save_path}"))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.update_progress(0, "")

    def _image_to_json(self, image_path, base_name, frame_number):
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            return {
                "name": f"Frame_{base_name}_{frame_number}",
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                "soft": False,
                "image_data": f"data:image/png;base64,{img_str}"
            }
        except Exception as e:
            self.master.after(0, lambda: messagebox.showwarning("Image Processing Error", f"Error processing {image_path}: {str(e)}"))
            return None

    def convert_to_gif(self):
        if not self.files:
            messagebox.showerror("Error", "Please add images first.")
            return

        duration = simpledialog.askinteger("Frame Duration", "Enter frame duration (in milliseconds):", 
                                           minvalue=10, maxvalue=1000, initialvalue=100)
        if not duration:
            return

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_file:
            temp_path = temp_file.name

        threading.Thread(target=self._process_images_to_gif, args=(temp_path, duration)).start()

    def _process_images_to_gif(self, save_path, duration):
        try:
            frames = []
            total_steps = sum(repeat for _, _, _, repeat, _ in self.files) + 1  # +1 for saving
            current_step = 0

            self.update_progress(0, "Starting conversion to GIF...")

            for _, path, _, repeat, _ in self.files:
                try:
                    with Image.open(path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        for _ in range(repeat):
                            frames.append(img.copy())
                            current_step += 1
                            self.update_progress((current_step / total_steps) * 100,
                                                 f"Processing frame {current_step} of {total_steps - 1}")
                except Exception as e:
                    self.master.after(0, lambda: messagebox.showwarning("Image Processing Error", f"Error processing {path}: {str(e)}"))

            if not frames:
                self.master.after(0, lambda: messagebox.showerror("Error", "No valid images to convert to GIF."))
                return

            self.update_progress(100, "Saving GIF...")

            frames[0].save(
                save_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0,
                optimize=False
            )

            self.update_progress(100, "Conversion complete! Opening preview...")

            self.master.after(0, lambda: self.show_gif_preview(save_path))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.update_progress(0, "")

    def show_gif_preview(self, temp_path):
        try:
            preview_window = GifPreviewWindow(self.master, temp_path)
            self.master.wait_window(preview_window)

            if preview_window.result:
                final_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
                if final_path:
                    try:
                        shutil.move(temp_path, final_path)
                        messagebox.showinfo("Success", f"GIF saved as {final_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save GIF: {str(e)}")
                        # Eğer taşıma başarısız olursa, temp_path'i silmeyi dene
                        self.safe_remove(temp_path)
                else:
                    # Kullanıcı kaydetmeyi iptal ettiyse temp_path'i sil
                    self.safe_remove(temp_path)
            else:
                messagebox.showinfo("Cancelled", "GIF creation cancelled.")
                # Kullanıcı önizlemeyi kapattıysa temp_path'i sil
                self.safe_remove(temp_path)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.safe_remove(temp_path)
        finally:
            # Son bir kontrol daha yap
            if os.path.exists(temp_path):
                self.safe_remove(temp_path)

class JsonToGifConverter(BaseConverter):
    def __init__(self, master):
        super().__init__(master)
        self.tree.configure(columns=('Filename', 'Note'))
        self.tree.heading('Filename', text='File name')
        self.tree.heading('Note', text='Note')
        self.tree.column('Filename', width=400)
        self.tree.column('Note', width=200)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.tree.bind('<Double-1>', self.on_double_click)

    def create_buttons(self):
        buttons = [
            ("Add JSON", self.add_json_files),
            ("Remove", self.remove_selected),
            ("GIF", self.convert_to_gif),
            ("Merge JSONs", self.merge_json_files),
            ("Rename All", self.rename_all),
            ("Reverse", self.reverse_order),
            ("Undo", self.undo_last_action),
            ("Save", self.save_session),
            ("Load", self.load_session_dialog),
            ("Menu", self.back_to_main_menu_with_save_prompt)
        ]
        
        for i, (text, command) in enumerate(buttons):
            self.button_frame.grid_columnconfigure(i, weight=1)
            ttk.Button(self.button_frame, text=text, command=command).grid(column=i, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)

    def on_double_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            column = self.tree.identify_column(event.x)
            if column == '#1':  # Filename column
                self.open_file(item)
            elif column == '#2':  # Note column
                self.edit_note(item)

    def load_session_dialog(self):
        filename = filedialog.askopenfilename(filetypes=[("JFT files", "*.jft")])
        if filename:
            self.load_session(filename)

    def add_file(self, path):
        if path.lower().endswith('.json'):
            self.file_counter += 1
            original_filename = os.path.basename(path)
            new_filename = f"work_{self.file_counter}.json"
            
            # Yeni bir giriş oluştur
            item = self.tree.insert('', 'end', values=(new_filename, ''))
            self.files.append((item, path, new_filename, ''))
            self.undo_stack.append(('add', [(item, path, new_filename, '')]))
            self.changes_made = True
            
            self.tree.update()
            return item
        else:
            messagebox.showwarning("Invalid File", f"The file {path} is not a JSON file and will be skipped.")
            return None

    def add_json_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        added_items = []
        for path in file_paths:
            item = self.add_file(path)
            if item:
                added_items.append(item)
        if added_items:
            self.undo_stack.append(('add', added_items))
        self.sort_items()


    def merge_json_files(self):
        if not self.files:
            messagebox.showerror("Error", "No JSON files to merge.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not save_path:
            return

        threading.Thread(target=self._process_json_files, args=(save_path,)).start()


    def is_valid_file(self, path):
        return path.lower().endswith('.json')
    
    def _process_json_files(self, save_path):
        try:
            total_files = len(self.files)
            processed_files = 0

            self.update_progress(0, "Starting JSON merge...")

            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_file.write('[')
                first_item = True
                for _, path, _, _ in self.files:
                    try:
                        with open(path, 'r') as f:
                            json_data = json.load(f)
                        if isinstance(json_data, dict) and 'data' in json_data:
                            json_data = json_data['data']
                        elif not isinstance(json_data, list):
                            json_data = [json_data]
                        
                        for item in json_data:
                            if not first_item:
                                temp_file.write(',')
                            json.dump(item, temp_file)
                            first_item = False
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showwarning("JSON Processing Error", f"Error processing {path}: {str(e)}"))
                    
                    processed_files += 1
                    self.update_progress((processed_files / total_files) * 100,
                                         f"Processing file {processed_files} of {total_files}")
                temp_file.write(']')

            self.update_progress(100, "Saving merged JSON file...")

            os.replace(temp_file.name, save_path)
            
            self.update_progress(100, "Merge complete!")
            self.master.after(0, lambda: messagebox.showinfo("Success", f"Merged JSON file saved as {save_path}"))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.update_progress(0, "")

    def convert_to_gif(self):
        if not self.files:
            messagebox.showerror("Error", "Please add JSON files first.")
            return

        duration = simpledialog.askinteger("Frame Duration", "Enter frame duration (in milliseconds):", 
                                           minvalue=10, maxvalue=1000, initialvalue=100)
        if not duration:
            return

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_file:
            temp_path = temp_file.name

        threading.Thread(target=self._process_json_files_to_gif, args=(temp_path, duration)).start()


    def _process_json_files_to_gif(self, save_path, duration):
        try:
            frames = []
            total_files = len(self.files)
            processed_files = 0

            self.update_progress(0, "Starting conversion to GIF...")

            for _, path, _, _ in self.files:
                try:
                    with open(path, 'r') as f:
                        json_data = json.load(f)
                    
                    if isinstance(json_data, dict) and 'data' in json_data:
                        json_data = json_data['data']
                    elif not isinstance(json_data, list):
                        json_data = [json_data]
                    
                    for item in json_data:
                        image_data = item.get('image_data', '')
                        if image_data.startswith('data:image/'):
                            _, base64_data = image_data.split(',', 1)
                            image_bytes = base64.b64decode(base64_data)
                            img = Image.open(io.BytesIO(image_bytes))
                            frames.append(img.convert('RGBA'))
                
                except Exception as e:
                    self.master.after(0, lambda: messagebox.showwarning("JSON Processing Error", f"Error processing {path}: {str(e)}"))
                
                processed_files += 1
                self.update_progress((processed_files / total_files) * 100,
                                     f"Processing file {processed_files} of {total_files}")

            if not frames:
                self.master.after(0, lambda: messagebox.showerror("Error", "No valid images found in JSON files."))
                return

            self.update_progress(100, "Saving GIF...")

            frames[0].save(
                save_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0,
                optimize=False
            )

            self.update_progress(100, "Conversion complete! Opening preview...")

            self.master.after(0, lambda: self.show_gif_preview(save_path))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.update_progress(0, "")
    
    def show_gif_preview(self, temp_path):
        preview_window = GifPreviewWindow(self.master, temp_path)
        self.master.wait_window(preview_window)

        if preview_window.result:
            final_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
            if final_path:
                try:
                    os.replace(temp_path, final_path)
                    messagebox.showinfo("Success", f"GIF saved as {final_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save GIF: {str(e)}")
                    self.safe_remove(temp_path)
            else:
                self.safe_remove(temp_path)
        else:
            self.safe_remove(temp_path)

class TipsViewer(BaseConverter):
    def __init__(self, master):
        super().__init__(master)
        self.create_tips_widgets()

    def create_widgets(self):
        # BaseConverter'ın widget'larını oluşturmasına izin ver
        super().create_widgets()

    def create_tips_widgets(self):
        # Mevcut widget'ları temizle
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.tips_text = tk.Text(self.frame, wrap=tk.WORD, width=80, height=20)
        self.tips_text.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.tips_text.insert(tk.END, self.get_tips())
        self.tips_text.config(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tips_text.yview)
        scrollbar.grid(column=1, row=0, sticky=(tk.N, tk.S))
        self.tips_text.configure(yscrollcommand=scrollbar.set)

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        ttk.Button(self.frame, text="Back to Main Menu", command=self.back_to_main_menu_with_save_prompt).grid(column=0, row=1, sticky=(tk.W, tk.E), pady=10)

    def get_tips(self):
        return """
Tips for Using JFT (JSON and File Tools):

1. Image Converter (Animation):
   - Use this tool to convert a series of images into a JSON file or GIF.
   - You can drag and drop image files directly into the application.
   - Set repeat counts for each image to control how long it appears in the animation.
   - The 'Convert to JSON' option creates a JSON file suitable for use with certain animation tools.
   - The 'Convert to GIF' option creates a standard animated GIF file.
   - Double-click on the 'Note' column to add notes to each image.

2. JSON to GIF Converter (Save History):
   - This tool is useful for converting JSON files (like those created by the Image Converter) into GIF files.
   - You can also use it to merge multiple JSON files into a single file.
   - Drag and drop JSON files into the application for easy adding.
   - Double-click on the 'Note' column to add notes to each JSON file.

General Tips:
- You can select multiple files at once when adding images or JSON files.
- Use the 'Rename All' feature to quickly rename a series of files with a common base name.
- The 'Undo' button allows you to reverse your last action in case of mistakes.
- Double-click on a filename to open the file in your default application.
- For Image Converter, double-click on the 'Repeat' column to edit the repeat count for an individual image.

Shortcuts:
- Ctrl+Z: Undo the last action
- Backspace: Remove selected items from the list
- Ctrl+A: Select All

Remember to always keep backups of your original files before performing any conversions or merges!!!
"""

    def create_buttons(self):
        # This method is required by BaseConverter but not used in TipsViewer
        pass

    def add_file(self, path):
        # This method is required by BaseConverter but not used in TipsViewer
        pass

    def process_dropped_items(self, paths):
        # This method is required by BaseConverter but not used in TipsViewer
        pass

class Application(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("JFT")
        self.geometry("600x400")
        self.resizable(False, False)
        self.main_frame = None
        self.current_converter = None
        self.show_main_menu()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def show_main_menu(self):
        if self.current_converter:
            self.current_converter.cleanup()
            self.current_converter = None
        
        if self.main_frame:
            self.main_frame.destroy()
            
        self.geometry("600x400")
        self.resizable(False, False)
        self.is_converter_open = False
    
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure('Large.TButton', font=('Helvetica', 14))

        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        buttons = [
            ("Image Converter\n     (Animation)", self.show_image_converter),
            ("JSON to GIF Converter\n         (Save History)", self.show_json_to_gif_converter),
            ("Tips for Using JFT", self.show_tips)
        ]

        for i, (text, command) in enumerate(buttons):
            button_frame.grid_rowconfigure(i, weight=1)
            btn = ttk.Button(button_frame, text=text, command=command, style='Large.TButton')
            btn.grid(row=i, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10 if i < len(buttons) - 1 else 0))

        button_frame.grid_columnconfigure(0, weight=1)

    def show_image_converter(self):
        self.main_frame.destroy()
        self.geometry("900x500")
        self.resizable(True, True)

        self.current_converter = ImageConverter(self)

    def show_json_to_gif_converter(self):
        self.main_frame.destroy()
        self.geometry("800x500")
        self.resizable(True, True)
        
        self.current_converter = JsonToGifConverter(self)
    
    def show_tips(self):
        self.main_frame.destroy()
        self.geometry("800x500")
        self.resizable(True, True)

        self.current_converter = TipsViewer(self)

    def on_closing(self):
        if self.current_converter:
            self.current_converter.on_closing()
        else:
            self.destroy()
        
if __name__ == "__main__":
    app = Application()
    app.mainloop()