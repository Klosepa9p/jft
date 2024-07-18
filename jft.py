import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64
import json
import datetime
import os
from PIL import Image
import io
import threading
import re
import platform
import subprocess

class Application(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("JFT")
        self.geometry("600x400")
        self.resizable(False, False)
        self.main_frame = None
        self.show_main_menu()

    def show_main_menu(self):
        if self.main_frame:
            self.main_frame.destroy()
        
        self.geometry("600x400")
        self.resizable(False, False)
        
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure('Large.TButton', font=('Helvetica', 14))

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_rowconfigure(0, weight=1)
        button_frame.grid_rowconfigure(1, weight=1)

        ttk.Button(button_frame, text="Image Converter\n    (Animation)", command=self.show_image_converter, style='Large.TButton').grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=0, pady=0)
        ttk.Button(button_frame, text="JSON to GIF Converter\n        (Save History)", command=self.show_json_to_gif_converter, style='Large.TButton').grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=0, pady=0)

    def show_image_converter(self):
        self.main_frame.destroy()
        self.geometry("900x500")
        self.resizable(None, None)
        ImageConverter(self)

    def show_json_to_gif_converter(self):
        self.main_frame.destroy()
        self.geometry("800x500")
        self.resizable(None, None)
        JsonToGifConverter(self)

class ImageConverter:
    def __init__(self, master):
        self.master = master
        self.images = []
        self.sort_order = True  # True for ascending, False for descending
        self.undo_stack = []
        self.create_widgets()

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        # Create a separate frame for buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(column=0, row=0, sticky=(tk.W, tk.E))
        for i in range(8):
            button_frame.grid_columnconfigure(i, weight=1)

        # Add buttons to the button frame
        ttk.Button(button_frame, text="Add Images", command=self.add_images).grid(column=0, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Set All Repeats", command=self.set_all_repeats).grid(column=2, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Convert to JSON", command=self.convert_to_json).grid(column=3, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Convert to GIF", command=self.convert_to_gif).grid(column=4, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Reverse Order", command=self.reverse_order).grid(column=5, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Rename All", command=self.rename_all).grid(column=6, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Undo", command=self.undo_last_action).grid(column=7, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Back to Main Menu", command=self.back_to_main_menu).grid(column=8, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)


        # Treeview setup
        self.tree = ttk.Treeview(self.frame, columns=('Filename', 'Repeat'), show='headings')
        self.tree.heading('Filename', text='Image Filename')
        self.tree.heading('Repeat', text='Repeat Count')
        self.tree.column('Filename', width=600)
        self.tree.column('Repeat', width=100)
        self.tree.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(column=1, row=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<BackSpace>', self.remove_selected)  # Changed from Delete to BackSpace

        # Progress bar
        self.progress = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(column=0, row=2, sticky=(tk.W, tk.E), pady=5)

        # Status label
        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(column=0, row=3, sticky=(tk.W, tk.E))

        # Enable drag and drop
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop)

    def natural_sort_key(self, s):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

    def sort_items(self):
        items = [(self.tree.set(k, 'Filename'), k) for k in self.tree.get_children('')]
        items.sort(key=lambda x: self.natural_sort_key(x[0]), reverse=not self.sort_order)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        
        self.images.sort(key=lambda x: self.natural_sort_key(x[2]), reverse=not self.sort_order)

    def drop(self, event):
        files = self.tree.tk.splitlist(event.data)
        for file in files:
            self.add_image(file)
        self.sort_items()

    def add_image(self, path):
        if self.is_valid_image(path):
            filename = os.path.basename(path)
            item = self.tree.insert('', 'end', values=(filename, 1))
            self.images.append((item, path, filename, 1))
        else:
            messagebox.showwarning("Invalid Image", f"The file {path} is not a valid image and will be skipped.")

    def back_to_main_menu(self):
        self.frame.destroy()
        self.master.show_main_menu()

    def add_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        for path in file_paths:
            self.add_image(path)
        self.sort_items()

    def is_valid_image(self, path):
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except:
            return False

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        if column == '#2':  # Repeat Count column
            self.edit_repeat_count(item)
        else:  # Filename column
            self.open_image(item)

    def open_image(self, item):
        image_info = next((img for img in self.images if img[0] == item), None)
        if image_info:
            try:
                if platform.system() == "Windows":
                    os.startfile(image_info[1])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", image_info[1]])
                else:  # Linux and other systems
                    subprocess.call(["xdg-open", image_info[1]])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")

    def edit_repeat_count(self, item):
        current_value = self.tree.set(item, 'Repeat')
        new_value = simpledialog.askinteger("Edit Repeat Count", "Enter new repeat count:", 
                                            initialvalue=current_value, minvalue=1, maxvalue=1000)
        if new_value is not None:
            self.tree.set(item, 'Repeat', new_value)
            for i, (tree_item, path, filename, _) in enumerate(self.images):
                if tree_item == item:
                    self.images[i] = (tree_item, path, filename, new_value)
                    break

    def remove_selected(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        removed_items = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            removed_items.append((item, values[0], values[1]))  # item, filename, repeat
            self.tree.delete(item)
            self.images = [img for img in self.images if img[0] != item]

        self.undo_stack.append(('remove', removed_items))

    def undo_last_action(self):
        if not self.undo_stack:
            return

        action, items = self.undo_stack.pop()
        if action == 'remove':
            for item, filename, repeat in items:
                insert_index = self.find_insert_index(filename)
                new_item = self.tree.insert('', insert_index, values=(filename, repeat))
                path = next((img[1] for img in self.images if img[2] == filename), None)
                if path:
                    self.images.append((new_item, path, filename, int(repeat)))
            self.sort_items()  # Eklenen öğelerden sonra listeyi yeniden sırala

    def find_insert_index(self, filename):
        for index, child in enumerate(self.tree.get_children()):
            if self.natural_sort_key(filename) < self.natural_sort_key(self.tree.item(child)['values'][0]):
                return index
        return 'end'

    def set_all_repeats(self):
        repeat_value = simpledialog.askinteger("Set All Repeats", "Enter repeat count for all images:", 
                                               minvalue=1, maxvalue=1000)
        if repeat_value is not None:
            for item in self.tree.get_children():
                self.tree.set(item, 'Repeat', repeat_value)
            self.images = [(item, path, filename, repeat_value) for item, path, filename, _ in self.images]

    def reverse_order(self):
        self.sort_order = not self.sort_order
        self.sort_items()

    def rename_all(self):
        if not self.images:
            messagebox.showerror("Error", "No images to rename.")
            return

        new_base_name = simpledialog.askstring("Rename Images", "Enter new base name for images:")
        if not new_base_name:
            return  # User cancelled or entered empty string

        for index, (item, old_path, _, repeat) in enumerate(self.images):
            directory = os.path.dirname(old_path)
            extension = os.path.splitext(old_path)[1]
            new_name = f"{new_base_name}_{index + 1}{extension}"
            new_path = os.path.join(directory, new_name)

            try:
                os.rename(old_path, new_path)
                self.tree.item(item, values=(new_name, repeat))
                self.images[index] = (item, new_path, new_name, repeat)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename {old_path}: {str(e)}")

        messagebox.showinfo("Rename Complete", "All images have been renamed.")

    def image_to_json(self, image_path, index):
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            return {
                "name": f"image_{index}",
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                "soft": False,
                "image_data": f"data:image/png;base64,{img_str}"
            }
        except Exception as e:
            messagebox.showwarning("Image Processing Error", f"Error processing {image_path}: {str(e)}")
            return None

    def convert_to_json(self):
        if not self.images:
            messagebox.showerror("Error", "Please add images first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not save_path:
            return

        def process_images():
            try:
                json_data = []
                total_images = sum(repeat for _, _, _, repeat in self.images)
                processed_images = 0
                image_index = 0

                # Reset progress bar and status
                self.progress['value'] = 0
                self.status_label['text'] = "Starting conversion to JSON..."
                self.master.update_idletasks()

                for _, path, _, repeat in self.images:
                    image_json = self.image_to_json(path, image_index)
                    if image_json:
                        for _ in range(repeat):
                            json_data.append(image_json)
                            processed_images += 1
                            self.progress['value'] = (processed_images / total_images) * 100
                            self.status_label['text'] = f"Processing image {processed_images} of {total_images}"
                            self.master.update_idletasks()
                    image_index += 1

                if not json_data:
                    messagebox.showerror("Error", "No valid images to convert.")
                    return

                self.status_label['text'] = "Saving JSON file..."
                self.master.update_idletasks()

                with open(save_path, "w") as f:
                    json.dump(json_data, f, indent=2)
                
                self.progress['value'] = 100
                self.status_label['text'] = "Conversion complete!"
                self.master.update_idletasks()
                
                self.master.after(0, lambda: messagebox.showinfo("Success", f"JSON file saved as {save_path}"))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            finally:
                self.progress['value'] = 0
                self.status_label['text'] = ""

        threading.Thread(target=process_images).start()

    def convert_to_gif(self):
        if not self.images:
            messagebox.showerror("Error", "Please add images first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
        if not save_path:
            return

        duration = simpledialog.askinteger("Frame Duration", "Enter frame duration (in milliseconds):", 
                                           minvalue=10, maxvalue=1000, initialvalue=100)
        if not duration:
            return

        def process_images():
            try:
                frames = []
                total_steps = sum(repeat for _, _, _, repeat in self.images) + 1  # +1 for saving
                current_step = 0

                # Reset progress bar and status
                self.progress['value'] = 0
                self.status_label['text'] = "Starting conversion to GIF..."
                self.master.update_idletasks()

                for _, path, _, repeat in self.images:
                    try:
                        with Image.open(path) as img:
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            for _ in range(repeat):
                                frames.append(img.copy())
                                current_step += 1
                                self.progress['value'] = (current_step / total_steps) * 100
                                self.status_label['text'] = f"Processing frame {current_step} of {total_steps - 1}"
                                self.master.update_idletasks()
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showwarning("Image Processing Error", f"Error processing {path}: {str(e)}"))

                if not frames:
                    self.master.after(0, lambda: messagebox.showerror("Error", "No valid images to convert to GIF."))
                    return

                self.status_label['text'] = "Saving GIF..."
                self.master.update_idletasks()

                def save_callback(current):
                    nonlocal current_step
                    current_step = total_steps - 1 + (current / len(frames))
                    self.progress['value'] = (current_step / total_steps) * 100
                    self.status_label['text'] = f"Saving GIF: {int((current / len(frames)) * 100)}% complete"
                    self.master.update_idletasks()

                frames[0].save(
                    save_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration,
                    loop=0,
                    optimize=False,
                    progress_callback=save_callback
                )

                self.progress['value'] = 100
                self.status_label['text'] = "Conversion complete!"
                self.master.update_idletasks()
                self.master.after(0, lambda: messagebox.showinfo("Success", f"GIF saved as {save_path}"))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            finally:
                self.progress['value'] = 0
                self.status_label['text'] = ""

        threading.Thread(target=process_images).start()

class JsonToGifConverter:
    def __init__(self, master):
        self.master = master
        self.json_files = []
        self.sort_order = True  # True for ascending, False for descending
        self.undo_stack = []
        self.create_widgets()

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        # Create a separate frame for buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(column=0, row=0, sticky=(tk.W, tk.E))
        for i in range(7):
            button_frame.grid_columnconfigure(i, weight=1)

        # Add buttons to the button frame
        ttk.Button(button_frame, text="Add JSON Files", command=self.add_json_files).grid(column=0, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Convert to GIF", command=self.convert_to_gif).grid(column=2, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Merge JSONs", command=self.merge_json_files).grid(column=3, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Rename All", command=self.rename_all).grid(column=4, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Reverse Order", command=self.reverse_order).grid(column=5, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Undo", command=self.undo_last_action).grid(column=6, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        ttk.Button(button_frame, text="Back to Main Menu", command=self.back_to_main_menu).grid(column=7, row=0, sticky=(tk.W, tk.E), padx=2, pady=2)


        # Treeview setup
        self.tree = ttk.Treeview(self.frame, columns=('Filename',), show='headings')
        self.tree.heading('Filename', text='JSON Filename')
        self.tree.column('Filename', width=700)
        self.tree.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(column=1, row=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<BackSpace>', self.remove_selected)  # Changed from Delete to BackSpace

        # Progress bar
        self.progress = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(column=0, row=2, sticky=(tk.W, tk.E), pady=5)

        # Status label
        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(column=0, row=3, sticky=(tk.W, tk.E))

        # Enable drag and drop
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.drop)

    def natural_sort_key(self, s):
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

    def sort_items(self):
        items = [(self.tree.set(k, 'Filename'), k) for k in self.tree.get_children('')]
        items.sort(key=lambda x: self.natural_sort_key(x[0]), reverse=not self.sort_order)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        
        self.json_files.sort(key=lambda x: self.natural_sort_key(x[2]), reverse=not self.sort_order)

    def drop(self, event):
        files = self.tree.tk.splitlist(event.data)
        for file in files:
            self.add_json_file(file)
        self.sort_items()

    def add_json_file(self, path):
        if path.lower().endswith('.json'):
            filename = os.path.basename(path)
            item = self.tree.insert('', 'end', values=(filename,))
            self.json_files.append((item, path, filename))
        else:
            messagebox.showwarning("Invalid File", f"The file {path} is not a JSON file and will be skipped.")

    def back_to_main_menu(self):
        self.frame.destroy()
        self.master.show_main_menu()

    def add_json_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        for path in file_paths:
            self.add_json_file(path)
        self.sort_items()

    def remove_selected(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        removed_items = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            removed_items.append((item, values[0]))  # item, filename
            self.tree.delete(item)
            self.json_files = [json_file for json_file in self.json_files if json_file[0] != item]

        self.undo_stack.append(('remove', removed_items))

    def undo_last_action(self):
        if not self.undo_stack:
            return

        action, items = self.undo_stack.pop()
        if action == 'remove':
            for item, filename in items:
                insert_index = self.find_insert_index(filename)
                new_item = self.tree.insert('', insert_index, values=(filename,))
                path = next((json_file[1] for json_file in self.json_files if json_file[2] == filename), None)
                if path:
                    self.json_files.append((new_item, path, filename))
            self.sort_items()  # Eklenen öğelerden sonra listeyi yeniden sırala

    def find_insert_index(self, filename):
        for index, child in enumerate(self.tree.get_children()):
            if self.natural_sort_key(filename) < self.natural_sort_key(self.tree.item(child)['values'][0]):
                return index
        return 'end'

    def reverse_order(self):
        self.sort_order = not self.sort_order
        self.sort_items()

    def rename_all(self):
        if not self.json_files:
            messagebox.showerror("Error", "No JSON files to rename.")
            return

        new_base_name = simpledialog.askstring("Rename JSON Files", "Enter new base name for JSON files:")
        if not new_base_name:
            return  # User cancelled or entered empty string

        for index, (item, old_path, _) in enumerate(self.json_files):
            directory = os.path.dirname(old_path)
            new_name = f"{new_base_name}_{index + 1}.json"
            new_path = os.path.join(directory, new_name)

            try:
                os.rename(old_path, new_path)
                self.tree.item(item, values=(new_name,))
                self.json_files[index] = (item, new_path, new_name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename {old_path}: {str(e)}")

        messagebox.showinfo("Rename Complete", "All JSON files have been renamed.")
        self.sort_items()

    def merge_json_files(self):
        if not self.json_files:
            messagebox.showerror("Error", "No JSON files to merge.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not save_path:
            return

        def process_json_files():
            try:
                merged_data = []
                total_files = len(self.json_files)
                processed_files = 0

                # Reset progress bar and status
                self.progress['value'] = 0
                self.status_label['text'] = "Starting JSON merge..."
                self.master.update_idletasks()

                for _, path, _ in self.json_files:
                    try:
                        with open(path, 'r') as f:
                            json_data = json.load(f)
                            if isinstance(json_data, list):
                                merged_data.extend(json_data)
                            else:
                                merged_data.append(json_data)
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showwarning("JSON Processing Error", f"Error processing {path}: {str(e)}"))
                    
                    processed_files += 1
                    self.progress['value'] = (processed_files / total_files) * 100
                    self.status_label['text'] = f"Processing file {processed_files} of {total_files}"
                    self.master.update_idletasks()

                if not merged_data:
                    messagebox.showerror("Error", "No valid data to merge.")
                    return

                # Add the "name" field to the merged data
                final_data = {
                    "name": "myHistory",
                    "data": merged_data
                }

                self.status_label['text'] = "Saving merged JSON file..."
                self.master.update_idletasks()

                with open(save_path, "w") as f:
                    json.dump(final_data, f, indent=2)
                
                self.progress['value'] = 100
                self.status_label['text'] = "Merge complete!"
                self.master.update_idletasks()
                
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Merged JSON file saved as {save_path}"))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            finally:
                self.progress['value'] = 0
                self.status_label['text'] = ""

        threading.Thread(target=process_json_files).start()

    def convert_to_gif(self):
        if not self.json_files:
            messagebox.showerror("Error", "Please add JSON files first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
        if not save_path:
            return

        duration = simpledialog.askinteger("Frame Duration", "Enter frame duration (in milliseconds):", 
                                           minvalue=10, maxvalue=1000, initialvalue=100)
        if not duration:
            return

        def process_json_files():
            try:
                frames = []
                total_files = len(self.json_files)
                processed_files = 0

                # Reset progress bar and status
                self.progress['value'] = 0
                self.status_label['text'] = "Starting conversion to GIF..."
                self.master.update_idletasks()

                for _, path, _ in self.json_files:
                    try:
                        with open(path, 'r') as f:
                            json_data = json.load(f)
                        
                        for item in json_data:
                            image_data = item.get('image_data', '')
                            if image_data.startswith('data:image/'):
                                # Extract base64 data
                                _, base64_data = image_data.split(',', 1)
                                image_bytes = base64.b64decode(base64_data)
                                img = Image.open(io.BytesIO(image_bytes))
                                frames.append(img.convert('RGBA'))
                    
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showwarning("JSON Processing Error", f"Error processing {path}: {str(e)}"))
                    
                    processed_files += 1
                    self.progress['value'] = (processed_files / total_files) * 100
                    self.status_label['text'] = f"Processing file {processed_files} of {total_files}"
                    self.master.update_idletasks()

                if not frames:
                    self.master.after(0, lambda: messagebox.showerror("Error", "No valid images found in JSON files."))
                    return

                self.status_label['text'] = "Saving GIF..."
                self.master.update_idletasks()

                frames[0].save(
                    save_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration,
                    loop=0,
                    optimize=False
                )

                self.progress['value'] = 100
                self.status_label['text'] = "Conversion complete!"
                self.master.update_idletasks()
                self.master.after(0, lambda: messagebox.showinfo("Success", f"GIF saved as {save_path}"))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            finally:
                self.progress['value'] = 0
                self.status_label['text'] = ""

        threading.Thread(target=process_json_files).start()

if __name__ == "__main__":
    app = Application()
    app.mainloop()