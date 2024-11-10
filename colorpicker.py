import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pyautogui
import keyboard
import threading  # For running background tasks in a separate thread

# Global variables to hold the image, zoom factor, and zoom box
zoom_factor = 2  # Set the zoom factor (higher means more zoom)
zoom_box = None  # Holds the canvas image for the zoomed-in area
zoom_dot = None  # Holds the canvas object for the dot at the center of the zoomed area

# Global variable to store the current color (RGB and Hex)
current_rgb = ""
current_hex = ""
img = None  # Global img variable to store the screenshot

# Global list to store grid line IDs for deletion
lines = []  # Store the line IDs for the grid in zoom

# Function to open the file dialog and load the image
def open_image():
    global canvas, img, img_tk, zoom_box, zoom_dot
    
    file_path = filedialog.askopenfilename(title="Open Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
    if file_path:
        img = Image.open(file_path)
        img.thumbnail((500, 500))  # Resize to fit the window (optional)
        img_tk = ImageTk.PhotoImage(img)
        
        # Clear the previous image and display the new one
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        canvas.img = img_tk  # Keep a reference to the image to prevent garbage collection
        canvas.config(width=img.width, height=img.height)

# Function to pick color from the image
def pick_color(event):
    global current_rgb, current_hex  # Use global variables to store the color
    
    if img is None:
        return  # Ensure that we have an image loaded before trying to pick a color
    
    # Get the position of the mouse click
    x, y = event.x, event.y
    
    # Get the color of the pixel at the clicked position
    color = img.getpixel((x, y))
    
    # Convert the color to RGB and Hex
    current_rgb = f"{color}"
    current_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    
    # Update the label with the color info
    color_label.config(text=f"RGB:{current_rgb}\nHex:{current_hex}")
    
    # Set the color of the display button (background)
    color_display.config(bg=current_hex, text=" ")  # Set background color and clear text

# Function to change cursor to "plus" when the mouse enters the image
def set_plus_cursor(event):
    canvas.config(cursor="plus")

# Function to reset cursor to default when the mouse leaves the image
def reset_cursor(event):
    canvas.config(cursor="")

# Function to zoom into the image based on mouse position
def zoom_in(event):
    global zoom_box, zoom_dot, lines  # Include lines to keep track of the grid lines

    if img is None:
        return  # Ensure that we have an image loaded before trying to zoom

    # Clear previous zoom box and lines
    canvas.delete(zoom_box)  # Delete the previous zoom box
    for line in lines:  # Delete each previous grid line
        canvas.delete(line)
    lines.clear()  # Clear the list of line IDs
    
    # Get the current mouse position
    x, y = event.x, event.y
    
    # Define the size of the zoomed area (smaller zoom width and height)
    zoom_width = 75  # Width of zoom area
    zoom_height = 75  # Height of zoom area
    
    # Crop the image to the area around the mouse
    left = max(x - zoom_width // 2, 0)
    upper = max(y - zoom_height // 2, 0)
    right = min(x + zoom_width // 2, img.width)
    lower = min(y + zoom_height // 2, img.height)

    cropped_image = img.crop((left, upper, right, lower))
    
    # Resize the cropped image to zoom in (we're reducing the zoom factor to make the zoomed area smaller)
    zoomed = cropped_image.resize((zoom_width * zoom_factor, zoom_height * zoom_factor), Image.Resampling.LANCZOS)
    zoomed_tk = ImageTk.PhotoImage(zoomed)

    # Create a new zoom box
    zoom_box = canvas.create_image(x + 10, y + 10, anchor=tk.NW, image=zoomed_tk)
    canvas.itemconfig(zoom_box, image=zoomed_tk)  # Keep a reference to prevent garbage collection

    # Keep a reference to the zoomed image to prevent garbage collection
    canvas.zoomed_image = zoomed_tk

    # Update the position of the zoomed image to follow the cursor
    canvas.coords(zoom_box, x + 10, y + 10)
    
    # Draw a grid over the zoomed image
    cell_size = 10  # Size of each cell in the zoomed grid
    for i in range(0, zoom_width * zoom_factor, cell_size):
        # Draw vertical lines
        line_id = canvas.create_line(x + 10 + i, y + 10, x + 10 + i, y + 10 + zoom_height * zoom_factor, fill="black")
        lines.append(line_id)  # Store the ID of the line for later deletion
        # Draw horizontal lines
        line_id = canvas.create_line(x + 10, y + 10 + i, x + 10 + zoom_width * zoom_factor, y + 10 + i, fill="black")
        lines.append(line_id)  # Store the ID of the line for later deletion

    # Draw or update the dot at the center of the zoomed area
    zoom_center_x = zoom_width * zoom_factor // 2
    zoom_center_y = zoom_height * zoom_factor // 2
    canvas.delete(zoom_dot)
    # Create the dot at the center of the zoomed area
    zoom_dot = canvas.create_oval(
        x + 10 + zoom_center_x - 5, 
        y + 10 + zoom_center_y - 5, 
        x + 10 + zoom_center_x + 5, 
        y + 10 + zoom_center_y + 5, 
        fill="red", outline="red"
    )

# Function to copy the selected color to the clipboard
def copy_color_to_clipboard(event=None):
    global current_rgb, current_hex
    
    if current_rgb and current_hex:
        # Clear the clipboard and append the color values
        root.clipboard_clear()
        root.clipboard_append(f"RGB:{current_rgb} Hex:{current_hex}")
        root.update()  # To make sure the clipboard updates immediately

        # Optional: Show a message or feedback
        print(f"Copied to clipboard: {current_rgb} {current_hex}")

# Function to take a screenshot and resize it when Win+Shift+O is pressed
def capture_screenshot():
    global img  # Ensure we modify the global img variable
    
    # Capture the screenshot
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.convert("RGB")  # Ensure it's in RGB mode
    
    # Optionally resize the screenshot
    new_width = int(screenshot.width * 0.5)  # For example, scale to 50% width
    new_height = int(screenshot.height * 0.5)  # Scale to 50% height
    screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    img = screenshot  # Assign to global img
    
    # Convert to Tkinter-compatible image
    img_tk = ImageTk.PhotoImage(screenshot)
    
    # Use `root.after()` to ensure that Tkinter updates the UI from the main thread
    def update_image():
        # Clear the previous image and display the screenshot
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        canvas.img = img_tk  # Keep a reference to the image to prevent garbage collection
        canvas.config(width=screenshot.width, height=screenshot.height)

    root.after(0, update_image)  # Schedule the image update in the main thread

# Function to run background tasks (like hotkeys) in a separate thread
def run_background_tasks():
    # Listen for Win+Shift+O to capture the screenshot
    keyboard.add_hotkey("win+shift+o", capture_screenshot)

icon = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAActJREFUeF7tmj1uAjEQheEeoYDUCCHSpM5ZkhpOwBVSk7OkpkJRlDpJwwFyA5CsnYKJZsde27sev6VCgl3xvvd59o/pBPw1Bc8/qQnARSiTZ7z53gigoiUgGdAaEcGAugG8vR9d8+v5nQv6sJj5Su3KN28ALAAenNfuYYJtA2ABaMFDTTA3A2ABSME3zfQ//Z5bp780E8wYAAsgNrg2E4o3ABYAD05rnRrV1jxv/qOZEc9PjzelF2sALAApeGjjZIDUPH1enAGwAPoOXpwBsACGCl6MAbAAQi9qtNs82rSXth/sKAALYGjluQm9GwALYHv4dHdvv78WroT97k9b1q2fd13zgxkAC4AH5w2EmpCq+d7OA2ABaMFDTUjdfHYDYAGEBpdGPc2GXM1nMwAWQKrg1Mz98se9fX1ZZT1ZS7ZzWABWgyebAbAArAePNgAWQC3BOxsAC6C24MEGwAKoNbi3AbAAag+uGgALACW4aAA8ACITC6Kv6/mohwtt/xYfATRPcjhherIjkbfSvPdRAA6Apj41zE2w1nznowAMACIkNc2XRu67t7HTXtr+311hWgKwADgpDsRq094GjAByLbZC95vsyVCh+dSfdQU957JGl/tnZgAAAABJRU5ErkJggg=="

# Create the main window
root = tk.Tk()
root.title("Color Picker from Image with Zoom")
img = tk.PhotoImage(data=icon)
root.tk.call('wm', 'iconphoto', root._w, img)
# Create a canvas to display the image
canvas = tk.Canvas(root)
canvas.pack(padx=10, pady=10)

# Button to open the image
open_button = tk.Button(root, text="Open Image", command=open_image)
open_button.pack(pady=10)

# Label to display the selected color in RGB and Hex
color_label = tk.Label(root, text="Selected color will appear here", width=30, height=5)
color_label.pack(pady=10)

# Button to display the color as a background color and copy to clipboard when clicked
color_display = tk.Button(root, text="Copy Color to Clipboard", width=30, height=5, command=copy_color_to_clipboard)
color_display.pack(pady=10)

# Bind mouse click event to pick color
canvas.bind("<Button-1>", pick_color)

# Bind mouse motion event to zoom into the image on the cursor
canvas.bind("<Motion>", zoom_in)

# Bind the cursor change events
canvas.bind("<Enter>", set_plus_cursor)  # When mouse enters the canvas
canvas.bind("<Leave>", reset_cursor)    # When mouse leaves the canvas

# Bind the color label click event to copy color to clipboard
color_label.bind("<Button-1>", copy_color_to_clipboard)

# Start background tasks in a separate thread
background_thread = threading.Thread(target=run_background_tasks, daemon=True)
background_thread.start()

# Run the Tkinter event loop
root.mainloop()
