import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import time
import hashlib
from cryptography.fernet import Fernet

class SteganographyApp:
    def __init__(self, master):
        self.master = master
        master.title("Steganography Application")
        master.geometry("800x600")
        master.configure(bg="#2f4155")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.master, text="MUSK: YOUR PRIVACY IS OUR PRIORITY", fg="black", font=("Times", 25, "italic", "bold")).pack(pady=20)
        
        button_frame = tk.Frame(self.master, bg="#2f4155")
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="ENCODE", height=2, width=23, bg="#ed3833", fg="black", command=self.open_encode_window).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="DECODE", height=2, width=23, bg="#00bd56", fg="white", command=self.open_decode_window).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Exit", height=2, width=23, bg="#1089ff", fg="white", command=self.exit_app).pack(side=tk.LEFT, padx=10)

    def open_encode_window(self):
        EncodeWindow(self.master)

    def open_decode_window(self):
        DecodeWindow(self.master)

    def exit_app(self):
        if messagebox.askyesno(None, 'Do you want to quit?'):
            self.master.destroy()

class EncodeWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Encode Message")
        self.window.geometry("720x660")
        self.window.configure(bg="#2f4155")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.window, text="Hide Text in Image", bg="#2f4155", fg="black", font="Times 18 italic bold").pack(pady=10)

        self.image_frame = tk.Frame(self.window, bd=3, bg="#742921", width=340, height=280, relief=tk.GROOVE)
        self.image_frame.pack(pady=10)
        self.image_label = tk.Label(self.image_frame, bg="#742921")
        self.image_label.pack()

        self.message_frame = tk.Frame(self.window, bd=3, bg="white", width=340, height=280, relief=tk.GROOVE)
        self.message_frame.pack(pady=10)
        self.message_label = tk.Label(self.message_frame, text="Enter Message:", bg="white", font="Times 12 bold")
        self.message_label.pack()
        self.message_text = tk.Text(self.message_frame, width=40, height=10)
        self.message_text.pack()

        self.key_frame = tk.Frame(self.window, bd=3, bg="#07493d", relief=tk.GROOVE)
        self.key_frame.pack(pady=10, fill=tk.X, padx=10)
        tk.Label(self.key_frame, text="Enter key (min 8 characters):", font="Times 12 bold", bg="#07493d").grid(row=0, column=0, padx=5, pady=5)
        self.key_entry = tk.Entry(self.key_frame, show="*", font="Times 12")
        self.key_entry.grid(row=0, column=1, padx=5, pady=5)

        self.stego_frame = tk.Frame(self.window, bd=3, bg="#07493d", relief=tk.GROOVE)
        self.stego_frame.pack(pady=10, fill=tk.X, padx=10)
        tk.Label(self.stego_frame, text="Enter name for stego image:", font="Times 12 bold", bg="#07493d").grid(row=0, column=0, padx=5, pady=5)
        self.stego_entry = tk.Entry(self.stego_frame, font="Times 12")
        self.stego_entry.grid(row=0, column=1, padx=5, pady=5)

        button_frame = tk.Frame(self.window, bg="#2f4155")
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Open Cover Image", width=20, bg="#097924", fg="black", command=self.open_cover_image).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Encode Text", width=20, bg="#4a0979", fg="black", command=self.encode_message).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Back", width=20, bg="#020024", fg="white", command=self.window.destroy).pack(side=tk.LEFT, padx=10)

    def open_cover_image(self):
        filename = filedialog.askopenfilename(initialdir=os.getcwd(), title='Select Cover Image (*.png)', filetypes=[("PNG file","*.png")])
        if filename:
            self.img = Image.open(filename)
            self.display_image(self.img)

    def display_image(self, img):
        img.thumbnail((340, 280))
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def encode_message(self):
        key = self.key_entry.get()
        message = self.message_text.get("1.0", tk.END).strip()
        stego_name = self.stego_entry.get()

        if len(key) < 8:
            messagebox.showerror("Error", "Key must be at least 8 characters long")
            return
        if not message:
            messagebox.showerror("Error", "Message cannot be empty")
            return
        if not stego_name:
            messagebox.showerror("Error", "Please provide a name for the stego image")
            return
        if not hasattr(self, 'img'):
            messagebox.showerror("Error", "Please select a cover image")
            return

        try:
            start_time = time.time()
            encrypted_message = self.encrypt_message(key, message)
            self.encode_to_image(encrypted_message)
            end_time = time.time()
            
            messagebox.showinfo("Success", f"Message successfully encoded into image.\nEncoding took {end_time - start_time:.2f} seconds")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def encrypt_message(self, key, message):
        key = hashlib.sha256(key.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(message.encode())

    def encode_to_image(self, encrypted_message):
        # Implementation of LSB steganography goes here
        # This is a placeholder for the actual encoding logic
        pass

class DecodeWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Decode Message")
        self.window.geometry("720x600")
        self.window.configure(bg="#2f4155")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.window, text="Decode Text from Image", bg="#2f4155", fg="black", font="Times 18 italic bold").pack(pady=10)

        self.image_frame = tk.Frame(self.window, bd=3, bg="#07493d", width=340, height=280, relief=tk.GROOVE)
        self.image_frame.pack(pady=10)
        self.image_label = tk.Label(self.image_frame, bg="#07493d")
        self.image_label.pack()

        self.key_frame = tk.Frame(self.window, bd=3, bg="#2d6722", relief=tk.GROOVE)
        self.key_frame.pack(pady=10, fill=tk.X, padx=10)
        tk.Label(self.key_frame, text="Enter your secret key:", bg="#2d6722", font="Times 12 bold").grid(row=0, column=0, padx=5, pady=5)
        self.key_entry = tk.Entry(self.key_frame, show="*", font="Times 12")
        self.key_entry.grid(row=0, column=1, padx=5, pady=5)

        button_frame = tk.Frame(self.window, bg="#2f4155")
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Open Stego Image", width=20, bg="#097924", fg="black", command=self.open_stego_image).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Decode Message", width=20, bg="#4a0979", fg="black", command=self.decode_message).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Back", width=20, bg="#020024", fg="white", command=self.window.destroy).pack(side=tk.LEFT, padx=10)

        self.message_frame = tk.Frame(self.window, bd=3, bg="white", width=340, height=280, relief=tk.GROOVE)
        self.message_frame.pack(pady=10)
        self.message_label = tk.Label(self.message_frame, text="Decoded Message:", bg="white", font="Times 12 bold")
        self.message_label.pack()
        self.message_text = tk.Text(self.message_frame, width=40, height=10)
        self.message_text.pack()

    def open_stego_image(self):
        filename = filedialog.askopenfilename(initialdir=os.getcwd(), title='Select Stego Image (*.png)', filetypes=[("PNG file","*.png")])
        if filename:
            self.stego_img = Image.open(filename)
            self.display_image(self.stego_img)

    def display_image(self, img):
        img.thumbnail((340, 280))
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def decode_message(self):
        key = self.key_entry.get()

        if len(key) < 8:
            messagebox.showerror("Error", "Key must be at least 8 characters long")
            return
        if not hasattr(self, 'stego_img'):
            messagebox.showerror("Error", "Please select a stego image")
            return

        try:
            start_time = time.time()
            encrypted_message = self.decode_from_image()
            message = self.decrypt_message(key, encrypted_message)
            end_time = time.time()

            self.message_text.delete("1.0", tk.END)
            self.message_text.insert(tk.END, message)
            
            messagebox.showinfo("Success", f"Message successfully decoded.\nDecoding took {end_time - start_time:.2f} seconds")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def decode_from_image(self):
        # Implementation of LSB steganography decoding goes here
        # This is a placeholder for the actual decoding logic
        return b"Encrypted message placeholder"

    def decrypt_message(self, key, encrypted_message):
        key = hashlib.sha256(key.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(encrypted_message).decode()

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()