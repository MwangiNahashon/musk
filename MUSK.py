import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter
import os
import time
import hashlib
import base64
import random
from cryptography.fernet import Fernet

MAGIC = b"MUSK"
HEADER_SIZE = 8  # 4 bytes magic + 4 bytes big-endian length

# --- Adaptive bit-depth thresholds on the blurred 3x3 local variance ---
# Tune these if you find the encoder is skipping too much or hiding too aggressively.
VAR_SKIP = 10      # below this: 0 bits (too smooth to hide safely)
VAR_2BIT = 100     # below this: 1 bit per channel
VAR_3BIT = 500     # below this: 2 bits per channel; above: 3 bits per channel


# ---------------- key derivation ----------------

def derive_fernet_key(password):
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def shuffle_seed(password):
    return int.from_bytes(
        hashlib.sha256(("seed:" + password).encode("utf-8")).digest()[:8], "big"
    )


def pixel_positions(width, height, password):
    positions = list(range(width * height))
    random.Random(shuffle_seed(password)).shuffle(positions)
    return positions


# ---------------- bit helpers ----------------

def bytes_to_bits(data):
    return [(b >> (7 - i)) & 1 for b in data for i in range(8)]


def bits_to_bytes(bits):
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        out.append(byte)
    return bytes(out)


# ---------------- texture analysis ----------------

def compute_variance_map(img):
    """Per-pixel local variance from a blurred grayscale version.

    Blurring (radius 1) removes our tiny LSB edits, so the encoder and decoder
    classify every pixel identically. Uses summed-area tables for O(1) per pixel.
    """
    blurred = img.convert("L").filter(ImageFilter.GaussianBlur(radius=1))
    w, h = blurred.size
    gray = list(blurred.getdata())

    W1 = w + 1
    integral = [0] * ((h + 1) * W1)
    integral_sq = [0] * ((h + 1) * W1)

    for y in range(h):
        row_sum = 0
        row_sum_sq = 0
        row_base = (y + 1) * W1
        prev_base = y * W1
        gray_base = y * w
        for x in range(w):
            v = gray[gray_base + x]
            row_sum += v
            row_sum_sq += v * v
            integral[row_base + x + 1] = integral[prev_base + x + 1] + row_sum
            integral_sq[row_base + x + 1] = integral_sq[prev_base + x + 1] + row_sum_sq

    var_map = [0.0] * (w * h)
    for y in range(h):
        y1 = y - 1 if y > 0 else 0
        y2 = y + 1 if y < h - 1 else h - 1
        iy1, iy2 = y1, y2 + 1
        base_top = iy1 * W1
        base_bot = iy2 * W1
        row_base = y * w
        for x in range(w):
            x1 = x - 1 if x > 0 else 0
            x2 = x + 1 if x < w - 1 else w - 1
            ix1, ix2 = x1, x2 + 1
            n = (ix2 - ix1) * (iy2 - iy1)
            s = (integral[base_bot + ix2] - integral[base_bot + ix1]
                 - integral[base_top + ix2] + integral[base_top + ix1])
            sq = (integral_sq[base_bot + ix2] - integral_sq[base_bot + ix1]
                  - integral_sq[base_top + ix2] + integral_sq[base_top + ix1])
            mean = s / n
            var_map[row_base + x] = max(0.0, (sq / n) - mean * mean)
    return var_map


def depth_for_variance(var):
    """Map local variance → number of LSBs to use per channel."""
    if var < VAR_SKIP:
        return 0
    if var < VAR_2BIT:
        return 1
    if var < VAR_3BIT:
        return 2
    return 3


# ---------------- adaptive LSB encode / decode ----------------

def embed_adaptive(img, payload, password):
    img = img.convert("RGB")
    w, h = img.size
    var_map = compute_variance_map(img)
    positions = pixel_positions(w, h, password)
    pixels = list(img.getdata())

    bits = bytes_to_bits(payload)
    total_bits = len(bits)

    # Capacity check
    capacity = 0
    for pos in positions:
        d = depth_for_variance(var_map[pos])
        if d > 0:
            capacity += d * 3
            if capacity >= total_bits:
                break
    if capacity < total_bits:
        raise ValueError(
            f"Message too long for this image.\n"
            f"Need {total_bits} bits, but capacity is only {capacity} bits.\n"
            f"Try a larger or more textured image."
        )

    bit_idx = 0
    used_pixels = 0
    for pos in positions:
        if bit_idx >= total_bits:
            break
        d = depth_for_variance(var_map[pos])
        if d == 0:
            continue
        r, g, b = pixels[pos][:3]
        ch = [r, g, b]
        for c in range(3):
            for k in range(d):
                if bit_idx >= total_bits:
                    break
                if ((ch[c] >> k) & 1) != bits[bit_idx]:
                    ch[c] ^= (1 << k)
                bit_idx += 1
        pixels[pos] = (ch[0], ch[1], ch[2])
        used_pixels += 1

    out = Image.new("RGB", (w, h))
    out.putdata(pixels)
    return out, used_pixels


def extract_adaptive(img, password):
    img = img.convert("RGB")
    w, h = img.size
    var_map = compute_variance_map(img)
    positions = pixel_positions(w, h, password)
    pixels = list(img.getdata())

    header_bits_needed = HEADER_SIZE * 8  # 64
    total_needed = None
    bits = []

    for pos in positions:
        d = depth_for_variance(var_map[pos])
        if d == 0:
            continue
        r, g, b = pixels[pos][:3]
        for c in (r, g, b):
            for k in range(d):
                bits.append((c >> k) & 1)

        if total_needed is None and len(bits) >= header_bits_needed:
            header = bits_to_bytes(bits[:header_bits_needed])
            if header[:4] != MAGIC:
                raise ValueError("No hidden message found, or the key is wrong.")
            length = int.from_bytes(header[4:8], "big")
            total_needed = header_bits_needed + length * 8

        if total_needed is not None and len(bits) >= total_needed:
            break

    if total_needed is None:
        raise ValueError("Could not find a readable header in the image.")
    if len(bits) < total_needed:
        raise ValueError("Image ended before the message was fully read.")

    payload_bits = bits[header_bits_needed:total_needed]
    return bits_to_bytes(payload_bits)


# ---------------- GUI ----------------

class SteganographyApp:
    def __init__(self, master):
        self.master = master
        master.title("MUSK Steganography")
        master.geometry("820x320")
        master.resizable(False, False)
        master.configure(bg="#2f4155")
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.master,
                 text="MUSK: YOUR PRIVACY IS OUR PRIORITY",
                 bg="#2f4155", fg="black",
                 font=("Times", 24, "italic", "bold")).pack(pady=40)

        frame = tk.Frame(self.master, bg="#2f4155")
        frame.pack(pady=10)

        tk.Button(frame, text="ENCODE", height=2, width=20, bg="#ed3833",
                  fg="black", font=("Times", 14, "bold"), bd=0,
                  command=self.open_encode).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="DECODE", height=2, width=20, bg="#00bd56",
                  fg="white", font=("Times", 14, "bold"), bd=0,
                  command=self.open_decode).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="EXIT", height=2, width=20, bg="#1089ff",
                  fg="white", font=("Times", 14, "bold"), bd=0,
                  command=self.exit_app).pack(side=tk.LEFT, padx=10)

    def open_encode(self):
        EncodeWindow(self.master)

    def open_decode(self):
        DecodeWindow(self.master)

    def exit_app(self):
        if messagebox.askyesno("Exit", "Do you want to quit?"):
            self.master.destroy()


class EncodeWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Encode Message")
        self.window.geometry("760x680")
        self.window.resizable(False, False)
        self.window.configure(bg="#2f4155")
        self.window.transient(master)
        self.window.grab_set()

        self.cover_img = None
        self._thumb_ref = None
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.window, text="Hide Text in Image (PNG only)",
                 bg="#2f4155", fg="black",
                 font=("Times", 18, "italic", "bold")).pack(pady=10)

        self.image_frame = tk.Frame(self.window, bd=3, bg="#742921",
                                    width=340, height=240, relief=tk.GROOVE)
        self.image_frame.pack(pady=5)
        self.image_frame.pack_propagate(False)
        self.image_label = tk.Label(self.image_frame, bg="#742921",
                                    text="No image selected", fg="white")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        msg_frame = tk.Frame(self.window, bd=3, bg="white", relief=tk.GROOVE)
        msg_frame.pack(pady=5, padx=10, fill=tk.X)
        tk.Label(msg_frame, text="Enter Message:", bg="white",
                 font=("Times", 12, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
        self.message_text = tk.Text(msg_frame, width=80, height=8, wrap=tk.WORD)
        self.message_text.pack(padx=5, pady=5, fill=tk.X)

        key_frame = tk.Frame(self.window, bd=3, bg="#07493d", relief=tk.GROOVE)
        key_frame.pack(pady=5, padx=10, fill=tk.X)
        tk.Label(key_frame, text="Secret key (min 8 chars):", bg="#07493d",
                 font=("Times", 12, "bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.key_entry = tk.Entry(key_frame, show="*", font=("Times", 12), width=30)
        self.key_entry.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        stego_frame = tk.Frame(self.window, bd=3, bg="#07493d", relief=tk.GROOVE)
        stego_frame.pack(pady=5, padx=10, fill=tk.X)
        tk.Label(stego_frame, text="Stego image name:", bg="#07493d",
                 font=("Times", 12, "bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.stego_entry = tk.Entry(stego_frame, font=("Times", 12), width=30)
        self.stego_entry.grid(row=0, column=1, padx=8, pady=6, sticky="w")
        self.stego_entry.insert(0, "stego")

        btn_frame = tk.Frame(self.window, bg="#2f4155")
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Open Cover Image", width=18, height=2,
                  bg="#097924", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.open_cover_image).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Encode", width=18, height=2,
                  bg="#4a0979", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.encode_message).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Back", width=18, height=2,
                  bg="#020024", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.window.destroy).pack(side=tk.LEFT, padx=6)

    def open_cover_image(self):
        filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Cover Image (*.png)",
            filetypes=[("PNG file", "*.png")],
        )
        if not filename:
            return
        try:
            self.cover_img = Image.open(filename).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image: {e}")
            return
        self.show_thumbnail(self.cover_img)

    def show_thumbnail(self, img):
        thumb = img.copy()
        thumb.thumbnail((340, 240))
        self._thumb_ref = ImageTk.PhotoImage(thumb)
        self.image_label.configure(image=self._thumb_ref, text="")
        self.image_label.image = self._thumb_ref

    def encode_message(self):
        key = self.key_entry.get()
        message = self.message_text.get("1.0", tk.END).strip()
        stego_name = self.stego_entry.get().strip()

        if not self.cover_img:
            messagebox.showerror("Error", "Please select a cover image first.")
            return
        if len(key) < 8:
            messagebox.showerror("Error", "Key must be at least 8 characters.")
            return
        if not message:
            messagebox.showerror("Error", "Message cannot be empty.")
            return
        if not stego_name:
            messagebox.showerror("Error", "Please provide a name for the stego image.")
            return

        if stego_name.lower().endswith(".png"):
            stego_name = stego_name[:-4]
        output_path = os.path.join(os.getcwd(), stego_name + ".png")

        try:
            start = time.time()

            fernet = Fernet(derive_fernet_key(key))
            ciphertext = fernet.encrypt(message.encode("utf-8"))

            payload = MAGIC + len(ciphertext).to_bytes(4, "big") + ciphertext

            stego_img, used_pixels = embed_adaptive(self.cover_img, payload, key)
            stego_img.save(output_path, "PNG")

            elapsed = time.time() - start
            messagebox.showinfo(
                "Success",
                f"Message encoded and saved to:\n{output_path}\n\n"
                f"Payload size: {len(ciphertext)} bytes\n"
                f"Pixels used (adaptive): {used_pixels} of {self.cover_img.width * self.cover_img.height}\n"
                f"Encoding took {elapsed:.2f}s",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))


class DecodeWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Decode Message")
        self.window.geometry("760x660")
        self.window.resizable(False, False)
        self.window.configure(bg="#2f4155")
        self.window.transient(master)
        self.window.grab_set()

        self.stego_img = None
        self._thumb_ref = None
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.window, text="Decode Text from Image",
                 bg="#2f4155", fg="black",
                 font=("Times", 18, "italic", "bold")).pack(pady=10)

        self.image_frame = tk.Frame(self.window, bd=3, bg="#07493d",
                                    width=340, height=240, relief=tk.GROOVE)
        self.image_frame.pack(pady=5)
        self.image_frame.pack_propagate(False)
        self.image_label = tk.Label(self.image_frame, bg="#07493d",
                                    text="No image selected", fg="white")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        key_frame = tk.Frame(self.window, bd=3, bg="#2d6722", relief=tk.GROOVE)
        key_frame.pack(pady=5, padx=10, fill=tk.X)
        tk.Label(key_frame, text="Secret key:", bg="#2d6722",
                 font=("Times", 12, "bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.key_entry = tk.Entry(key_frame, show="*", font=("Times", 12), width=30)
        self.key_entry.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        btn_frame = tk.Frame(self.window, bg="#2f4155")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Open Stego Image", width=18, height=2,
                  bg="#097924", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.open_stego_image).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Decode", width=18, height=2,
                  bg="#4a0979", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.decode_message).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Back", width=18, height=2,
                  bg="#020024", fg="white", bd=0, font=("Times", 12, "bold"),
                  command=self.window.destroy).pack(side=tk.LEFT, padx=6)

        out_frame = tk.Frame(self.window, bd=3, bg="white", relief=tk.GROOVE)
        out_frame.pack(pady=5, padx=10, fill=tk.X)
        tk.Label(out_frame, text="Decoded Message:", bg="white",
                 font=("Times", 12, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
        self.output_text = tk.Text(out_frame, width=80, height=8, wrap=tk.WORD)
        self.output_text.pack(padx=5, pady=5, fill=tk.X)

    def open_stego_image(self):
        filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Stego Image (*.png)",
            filetypes=[("PNG file", "*.png")],
        )
        if not filename:
            return
        try:
            self.stego_img = Image.open(filename).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image: {e}")
            return
        self.show_thumbnail(self.stego_img)

    def show_thumbnail(self, img):
        thumb = img.copy()
        thumb.thumbnail((340, 240))
        self._thumb_ref = ImageTk.PhotoImage(thumb)
        self.image_label.configure(image=self._thumb_ref, text="")
        self.image_label.image = self._thumb_ref

    def decode_message(self):
        key = self.key_entry.get()
        if len(key) < 8:
            messagebox.showerror("Error", "Key must be at least 8 characters.")
            return
        if not self.stego_img:
            messagebox.showerror("Error", "Please select a stego image first.")
            return

        try:
            start = time.time()
            payload = extract_adaptive(self.stego_img, key)
            ciphertext = payload  # header already stripped inside extract_adaptive

            fernet = Fernet(derive_fernet_key(key))
            message = fernet.decrypt(ciphertext).decode("utf-8")

            elapsed = time.time() - start
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, message)
            messagebox.showinfo("Success", f"Decoded in {elapsed:.2f}s")
        except Exception as e:
            messagebox.showerror("Error", f"Decoding failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()