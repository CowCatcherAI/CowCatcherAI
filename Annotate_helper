import os
import sys
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
from pathlib import Path

# Configuration - adjust these paths to match your project structure
model_path = "cowcatcher.pt"  # Path to your (latest) trained .pt model file
input_folder = "data/input"  # Folder containing images to be annotated
output_img_folder = "data/annotated_images"  # Folder for processed images with annotations
output_label_folder = "data/annotated_labels"  # Folder for label files corresponding to annotated images
delete_folder = "data/deleted"  # Folder for storing deleted/transferred images
enable_delete_mode = False  # Set to either False or True to enable image deletion functionality from start-up

class YoloAnnotationApp:
    def __init__(self, root, model_path, input_folder, output_img_folder, output_label_folder, delete_folder, enable_delete_mode):
        self.root = root
        self.root.title("CowCatcher Annotation Helper")
        self.root.geometry("1200x750")  # Slightly taller for new button
        
        # Set up folders and model path
        self.model_path = model_path
        self.input_folder = input_folder
        self.output_img_folder = output_img_folder
        self.output_label_folder = output_label_folder
        self.delete_folder = delete_folder
        self.delete_mode_enabled = enable_delete_mode
        
        # Create output folders if they don't exist
        os.makedirs(self.output_img_folder, exist_ok=True)
        os.makedirs(self.output_label_folder, exist_ok=True)
        os.makedirs(self.delete_folder, exist_ok=True)
        
        # Get all images
        self.image_files = [f for f in os.listdir(self.input_folder) 
                            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.current_index = 0
        
        # Variables for manual bounding box drawing
        self.drawing_mode = False
        self.start_x = None
        self.start_y = None
        self.current_rectangle = None
        self.manual_bbox = None
        self.current_img = None
        self.current_image_info = {}
        
        # Undo functionality
        self.last_action = None  # Stores info about the last action for undo
        
        # Load the YOLO model
        self.load_model()
        
        # UI setup
        self.setup_ui()
        
        # Load the first image
        if self.image_files:
            # Give the screen time to render before loading the first image
            self.root.update_idletasks()
            self.root.after(100, self.load_current_image)
    
    def load_model(self):
        try:
            # Try to import ultralytics YOLO first (for YOLOv8+)
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self.model_type = "ultralytics"
            print("Model loaded with ultralytics YOLO")
        except Exception as e:
            print(f"Error loading model with ultralytics: {e}")
            try:
                # Alternative method: torch.hub for older YOLOv5 models
                import torch
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path, force_reload=True)
                self.model_type = "torch_hub"
                print("Model loaded with torch.hub")
            except Exception as e2:
                print(f"Both loading methods failed: {e2}")
                raise Exception("Could not load YOLO model. Install 'pip install ultralytics'")
    
    def setup_ui(self):
        # Create frame for images
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Left: original image
        self.original_frame = ttk.LabelFrame(self.image_frame, text="Original Image")
        self.original_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        self.original_canvas = tk.Canvas(self.original_frame, highlightthickness=0)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right: image with predictions
        self.prediction_frame = ttk.LabelFrame(self.image_frame, text="Image with YOLO Predictions")
        self.prediction_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)
        self.prediction_canvas = tk.Canvas(self.prediction_frame, highlightthickness=0)
        self.prediction_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Event binding for mouse events (for manual drawing)
        self.original_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.original_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.original_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Create footer with buttons
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=10)
        
        # Status information
        self.status_label = ttk.Label(self.button_frame, text="")
        self.status_label.grid(row=0, column=0, columnspan=8, pady=5)
        
        # Delete mode toggle checkbox
        self.delete_mode_var = tk.BooleanVar(value=self.delete_mode_enabled)
        self.delete_mode_checkbox = ttk.Checkbutton(
            self.button_frame, 
            text="Enable Delete Mode", 
            variable=self.delete_mode_var,
            command=self.toggle_delete_mode
        )
        self.delete_mode_checkbox.grid(row=1, column=0, columnspan=8, pady=5)
        
        # Navigation and action buttons
        ttk.Button(self.button_frame, text="Previous (A)", command=self.prev_image).grid(row=2, column=0, padx=5)
        ttk.Button(self.button_frame, text="Next (D)", command=self.next_image).grid(row=2, column=1, padx=5)
        ttk.Button(self.button_frame, text="Save (S)", command=self.save_current).grid(row=2, column=2, padx=5)
        ttk.Button(self.button_frame, text="Null (N)", command=self.save_as_null).grid(row=2, column=3, padx=5)
        ttk.Button(self.button_frame, text="Skip (O)", command=self.skip_current).grid(row=2, column=4, padx=5)
        ttk.Button(self.button_frame, text="Draw (T)", command=self.toggle_drawing_mode).grid(row=2, column=5, padx=5)
        
        # Undo button
        self.undo_button = ttk.Button(self.button_frame, text="Undo (U)", command=self.undo_last_action)
        self.undo_button.grid(row=2, column=6, padx=5)
        self.undo_button.config(state='disabled')  # Initially disabled
        
        ttk.Button(self.button_frame, text="Exit (Q)", command=self.root.quit).grid(row=2, column=7, padx=5)
        
        # Keyboard shortcuts
        self.root.bind("<a>", lambda event: self.prev_image())
        self.root.bind("<A>", lambda event: self.prev_image())
        self.root.bind("<Left>", lambda event: self.prev_image())
        
        self.root.bind("<d>", lambda event: self.next_image())
        self.root.bind("<D>", lambda event: self.next_image())
        self.root.bind("<Right>", lambda event: self.next_image())
        
        self.root.bind("<s>", lambda event: self.save_current())
        self.root.bind("<S>", lambda event: self.save_current())
        
        self.root.bind("<n>", lambda event: self.save_as_null())
        self.root.bind("<N>", lambda event: self.save_as_null())
        
        self.root.bind("<o>", lambda event: self.skip_current())
        self.root.bind("<O>", lambda event: self.skip_current())
        
        self.root.bind("<t>", lambda event: self.toggle_drawing_mode())
        self.root.bind("<T>", lambda event: self.toggle_drawing_mode())
        
        # Undo shortcut
        self.root.bind("<u>", lambda event: self.undo_last_action())
        self.root.bind("<U>", lambda event: self.undo_last_action())
        
        # New: Delete shortcut removed
        
        self.root.bind("<Return>", lambda event: self.confirm_manual_bbox() if self.drawing_mode and self.manual_bbox else None)
        
        self.root.bind("<Q>", lambda event: self.root.quit())
        self.root.bind("<q>", lambda event: self.root.quit())
        self.root.bind("<Escape>", lambda event: self.root.quit())
    
    def toggle_delete_mode(self):
        """Toggle delete mode on/off"""
        self.delete_mode_enabled = self.delete_mode_var.get()
        
        status_text = "Delete mode enabled - processed images will be moved to DELETE folder" if self.delete_mode_enabled else "Delete mode disabled"
        self.status_label.config(text=status_text)
    
    def store_action_for_undo(self, action_type, img_filename, was_moved_to_delete=False):
        """Store information about the last action for potential undo"""
        self.last_action = {
            'type': action_type,  # 'save', 'null', 'skip', 'manual'
            'filename': img_filename,
            'was_moved_to_delete': was_moved_to_delete,
            'current_index': self.current_index
        }
        # Enable the undo button
        self.undo_button.config(state='normal')
    
    def undo_last_action(self):
        """Undo the last action performed"""
        if not self.last_action:
            self.status_label.config(text="No action to undo!")
            return
        
        action = self.last_action
        img_filename = action['filename']
        base_name = os.path.splitext(img_filename)[0]
        
        try:
            # Remove from annotated_images if it was saved there
            if action['type'] in ['save', 'null', 'manual']:
                annotated_img_path = os.path.join(self.output_img_folder, img_filename)
                if os.path.exists(annotated_img_path):
                    os.remove(annotated_img_path)
                    print(f"Removed from annotated_images: {img_filename}")
                
                # Remove label file
                label_path = os.path.join(self.output_label_folder, f"{base_name}.txt")
                if os.path.exists(label_path):
                    os.remove(label_path)
                    print(f"Removed label: {base_name}.txt")
            
            # Move back from DELETE folder if it was moved there
            if action['was_moved_to_delete']:
                delete_path = os.path.join(self.delete_folder, img_filename)
                input_path = os.path.join(self.input_folder, img_filename)
                
                if os.path.exists(delete_path):
                    shutil.move(delete_path, input_path)
                    print(f"Moved back from DELETE to input: {img_filename}")
                    
                    # Add back to image list if it's not already there
                    if img_filename not in self.image_files:
                        # Insert at the appropriate position to maintain order
                        self.image_files.insert(action['current_index'], img_filename)
                        print(f"Added back to image list: {img_filename}")
            
            # Update status and disable undo button
            self.status_label.config(text=f"Undid action for: {img_filename}")
            self.last_action = None
            self.undo_button.config(state='disabled')
            
            # Refresh the current view
            self.load_current_image()
            
        except Exception as e:
            print(f"Error during undo: {e}")
            self.status_label.config(text=f"Error during undo: {str(e)}")
    
    def move_to_delete_if_enabled(self, img_filename):
        """Move image to DELETE folder if delete mode is enabled"""
        if not self.delete_mode_enabled:
            return
            
        source_path = os.path.join(self.input_folder, img_filename)
        dest_path = os.path.join(self.delete_folder, img_filename)
        
        try:
            # Move the image to the DELETE folder
            shutil.move(source_path, dest_path)
            print(f"Image moved to DELETE: {img_filename}")
        except Exception as e:
            print(f"Error moving image to DELETE: {e}")
    
    def delete_current(self):
        """Move the current image to the DELETE folder"""
        if not self.delete_mode_enabled:
            self.status_label.config(text="Delete mode is disabled!")
            return
            
        if not self.image_files:
            return
        
        # Confirm deletion
        response = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to move '{self.image_files[self.current_index]}' to the DELETE folder?"
        )
        
        if not response:
            return
        
        img_filename = self.image_files[self.current_index]
        source_path = os.path.join(self.input_folder, img_filename)
        dest_path = os.path.join(self.delete_folder, img_filename)
        
        try:
            # Move the image to the DELETE folder
            shutil.move(source_path, dest_path)
            
            # Remove from the image list
            self.image_files.pop(self.current_index)
            
            # Adjust current index if necessary
            if self.current_index >= len(self.image_files):
                self.current_index = len(self.image_files) - 1
            
            self.status_label.config(text=f"Image moved to DELETE: {img_filename}")
            
            # Load the next image or show completion message
            if self.image_files:
                self.load_current_image()
            else:
                self.status_label.config(text="No more images to process!")
                
        except Exception as e:
            print(f"Error moving image to DELETE: {e}")
            self.status_label.config(text=f"Error: Could not move image - {str(e)}")
    
    def load_current_image(self):
        if not self.image_files:
            self.status_label.config(text="No images found!")
            return
        
        # Reset drawing mode and manual bounding box
        self.drawing_mode = False
        self.manual_bbox = None
        
        # Update status
        status_text = f"Image {self.current_index + 1} of {len(self.image_files)}: {self.image_files[self.current_index]}"
        if self.delete_mode_enabled:
            status_text += " | Delete mode: ON - processed images will be moved"
        self.status_label.config(text=status_text)
        
        # Load original image
        img_path = os.path.join(self.input_folder, self.image_files[self.current_index])
        original_img = cv2.imread(img_path)
        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        
        # Create a copy for prediction
        prediction_img = original_img.copy()
        
        # Perform YOLO prediction
        try:
            if self.model_type == "ultralytics":
                # For YOLOv8+ (ultralytics YOLO)
                results = self.model(img_path, conf=0.3)
            else:
                # For YOLOv5 (torch.hub)
                self.model.conf = 0.3
                results = self.model(img_path)
        except Exception as e:
            print(f"Error during prediction: {e}")
            results = None
        
        # Save results for later use
        self.current_results = results
        self.current_img_path = img_path
        self.current_img = original_img
        
        # Visualize the predictions
        self.draw_predictions(prediction_img, results)
        
        # Display images in the UI
        self.display_image(original_img, self.original_canvas)
        self.display_image(prediction_img, self.prediction_canvas)
    
    def draw_predictions(self, img, results):
        if results is None:
            cv2.putText(img, "Error processing predictions", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return
            
        try:
            if self.model_type == "ultralytics":
                # For YOLOv8+ (ultralytics YOLO)
                if len(results) > 0:
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            # Get bounding box coordinates
                            xyxy = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = map(int, xyxy)
                            conf = float(box.conf[0].cpu().numpy())
                            
                            # Draw bounding box
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            # Draw label with confidence
                            label = f"Mounting: {conf:.2f}"
                            cv2.putText(img, label, (x1, y1-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                # For YOLOv5 (torch.hub)
                for pred in results.xyxy[0].cpu().numpy():
                    x1, y1, x2, y2, conf, cls = pred
                    # Draw bounding box
                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    # Draw label with confidence
                    label = f"Mounting: {conf:.2f}"
                    cv2.putText(img, label, (int(x1), int(y1)-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        except Exception as e:
            print(f"Error drawing predictions: {e}")
            cv2.putText(img, f"Error: {str(e)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_image(self, cv_img, canvas):
        """Displays an image centered on the canvas with maximum size from the beginning"""
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 500  # Use 500 as fallback
        canvas_height = canvas.winfo_height() or 500  # Use 500 as fallback
        
        # Resize image for display but maintain aspect ratio
        height, width = cv_img.shape[:2]
        
        # Calculate scale factor to fit the image
        scale = min(canvas_width / width, canvas_height / height) * 0.9
        
        # New dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize image
        if scale != 1.0:
            cv_img = cv2.resize(cv_img, (new_width, new_height))
        
        # Convert to PIL and then to Tkinter-compatible format
        pil_img = Image.fromarray(cv_img)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        # Clear the canvas
        canvas.delete("all")
        
        # Calculate centering on the canvas
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        
        # Add the image to the canvas
        canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=tk_img)
        canvas.image = tk_img  # Prevent garbage collection
        
        # Save dimensions for coordinate conversion
        self.current_image_info = {
            'width': width,
            'height': height,
            'display_width': new_width,
            'display_height': new_height,
            'x_offset': x_offset,
            'y_offset': y_offset,
            'scale': scale
        }
    
    def next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            
    def skip_current(self):
        """Skips the current image and moves to the next one"""
        img_filename = self.image_files[self.current_index]
        
        # Store action for undo
        was_moved = self.delete_mode_enabled
        self.store_action_for_undo('skip', img_filename, was_moved)
        
        # Move to DELETE folder if delete mode is enabled
        self.move_to_delete_if_enabled(img_filename)
        
        self.status_label.config(text=f"Image skipped: {img_filename}")
        self.next_image()
    
    def save_current(self):
        """Saves the image with the model's predicted bounding box or with manual bounding box"""
        if not self.image_files:
            return
            
        # If we're in drawing mode with a manual bounding box, use that
        if self.drawing_mode and self.manual_bbox:
            self.save_with_manual_bbox()
            return
        
        # Filename without extension for label
        img_filename = self.image_files[self.current_index]
        base_name = os.path.splitext(img_filename)[0]
        
        # Copy image to output folder
        img_dest = os.path.join(self.output_img_folder, img_filename)
        try:
            shutil.copy2(self.current_img_path, img_dest)
        except Exception as e:
            print(f"Error copying image: {e}")
            self.status_label.config(text=f"Error: Could not copy image - {str(e)}")
            return
        
        # Create label file
        label_path = os.path.join(self.output_label_folder, f"{base_name}.txt")
        
        # Check if there are predictions and write the label
        try:
            self.write_label_file(label_path)
            
            # Store action for undo
            was_moved = self.delete_mode_enabled
            self.store_action_for_undo('save', img_filename, was_moved)
            
            # Move to DELETE folder if delete mode is enabled
            self.move_to_delete_if_enabled(img_filename)
            
            self.status_label.config(text=f"Image saved: {img_filename}")
            self.next_image()
        except Exception as e:
            print(f"Error writing label file: {e}")
            self.status_label.config(text=f"Error: Could not write label - {str(e)}")
    
    def save_as_null(self):
        """Saves the image with an empty label file, regardless of what the model detected"""
        if not self.image_files:
            return
        
        # Filename without extension for label
        img_filename = self.image_files[self.current_index]
        base_name = os.path.splitext(img_filename)[0]
        
        # Copy image to output folder
        img_dest = os.path.join(self.output_img_folder, img_filename)
        try:
            shutil.copy2(self.current_img_path, img_dest)
        except Exception as e:
            print(f"Error copying image: {e}")
            self.status_label.config(text=f"Error: Could not copy image - {str(e)}")
            return
        
        # Create an empty label file
        label_path = os.path.join(self.output_label_folder, f"{base_name}.txt")
        open(label_path, 'w').close()
        
        # Store action for undo
        was_moved = self.delete_mode_enabled
        self.store_action_for_undo('null', img_filename, was_moved)
        
        # Move to DELETE folder if delete mode is enabled
        self.move_to_delete_if_enabled(img_filename)
        
        self.status_label.config(text=f"Image saved as NULL (no mounting): {img_filename}")
        self.next_image()
    
    def write_label_file(self, label_path):
        # Read image for dimensions
        img = cv2.imread(self.current_img_path)
        height, width = img.shape[:2]
        
        has_detections = False
        
        if self.model_type == "ultralytics":
            # For YOLOv8+ (ultralytics YOLO)
            if len(self.current_results) > 0 and len(self.current_results[0].boxes) > 0:
                # Take the first (best) detection
                box = self.current_results[0].boxes[0]
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                # Convert to YOLO format (x_center, y_center, width, height)
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height
                
                # Write to label file (class_id x_center y_center width height)
                with open(label_path, 'w') as f:
                    f.write(f"0 {x_center} {y_center} {w} {h}")
                
                has_detections = True
        else:
            # For YOLOv5 (torch.hub)
            detections = self.current_results.xyxy[0].cpu().numpy()
            if len(detections) > 0:
                # Take the first (best) detection
                best_detection = detections[0]
                x1, y1, x2, y2, conf, cls = best_detection
                
                # Convert to YOLO format (x_center, y_center, width, height)
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height
                
                # Write to label file (class_id x_center y_center width height)
                with open(label_path, 'w') as f:
                    f.write(f"0 {x_center} {y_center} {w} {h}")
                
                has_detections = True
        
        # If there are no detections, create an empty label file
        if not has_detections:
            open(label_path, 'w').close()
            
    # Functions for manually drawing bounding boxes
    def toggle_drawing_mode(self):
        """Toggles drawing mode on/off"""
        if self.drawing_mode and self.manual_bbox:
            # If we're in drawing mode and have a bounding box, ask for confirmation
            response = messagebox.askyesnocancel(
                "Confirm Drawing", 
                "Do you want to save this bounding box?\n\nYes = Save and continue\nNo = Redraw\nCancel = Exit drawing mode"
            )
            
            if response is True:  # Yes: save and continue
                self.save_with_manual_bbox()
                return
            elif response is False:  # No: redraw
                self.manual_bbox = None
                if self.current_rectangle:
                    self.original_canvas.delete(self.current_rectangle)
                    self.current_rectangle = None
                self.status_label.config(text="Draw a new bounding box")
                return
            else:  # Cancel: exit drawing mode
                self.drawing_mode = False
                self.load_current_image()
                self.status_label.config(text=f"Drawing mode disabled")
                return
                
        # Toggle drawing mode
        self.drawing_mode = not self.drawing_mode
        
        # Reset existing bounding box when turning on drawing mode
        if self.drawing_mode:
            # Reset current drawing and predictions
            self.manual_bbox = None
            if self.current_rectangle:
                self.original_canvas.delete(self.current_rectangle)
                self.current_rectangle = None
            # Refresh the image without predictions
            self.display_image(self.current_img, self.original_canvas)
            self.status_label.config(text="Drawing mode active: Draw a bounding box with the mouse. Press Enter to confirm.")
        else:
            # Return to normal view
            self.load_current_image()
            self.status_label.config(text=f"Drawing mode disabled")
    
    def confirm_manual_bbox(self):
        """Confirms the manually drawn bounding box and continues"""
        if not self.drawing_mode or not self.manual_bbox:
            return
        
        response = messagebox.askyesno(
            "Confirm Drawing", 
            "Do you want to save this bounding box and continue to the next image?"
        )
        
        if response:
            self.save_with_manual_bbox()
    
    def on_mouse_down(self, event):
        """Handler for mouse down event"""
        if not self.drawing_mode:
            return
            
        # Start a new rectangle
        self.start_x = event.x
        self.start_y = event.y
        
        # Remove existing rectangle if there is one
        if self.current_rectangle:
            self.original_canvas.delete(self.current_rectangle)
            self.manual_bbox = None
        
        # Create a new rectangle
        self.current_rectangle = self.original_canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
    
    def on_mouse_drag(self, event):
        """Handler for mouse drag event"""
        if not self.drawing_mode or not self.current_rectangle:
            return
            
        # Update the rectangle during dragging
        self.original_canvas.coords(self.current_rectangle, self.start_x, self.start_y, event.x, event.y)
    
    def on_mouse_up(self, event):
        """Handler for mouse up event"""
        if not self.drawing_mode or not self.current_rectangle:
            return
            
        # Get the final coordinates
        end_x, end_y = event.x, event.y
        
        # Ensure the rectangle has positive width and height
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # Update the rectangle coordinates
        self.original_canvas.coords(self.current_rectangle, x1, y1, x2, y2)
        
        # Convert canvas coordinates to image coordinates
        x1_img = (x1 - self.current_image_info['x_offset']) / self.current_image_info['scale']
        y1_img = (y1 - self.current_image_info['y_offset']) / self.current_image_info['scale']
        x2_img = (x2 - self.current_image_info['x_offset']) / self.current_image_info['scale']
        y2_img = (y2 - self.current_image_info['y_offset']) / self.current_image_info['scale']
        
        # Constrain coordinates to stay within the image
        x1_img = max(0, min(x1_img, self.current_image_info['width']))
        y1_img = max(0, min(y1_img, self.current_image_info['height']))
        x2_img = max(0, min(x2_img, self.current_image_info['width']))
        y2_img = max(0, min(y2_img, self.current_image_info['height']))
        
        # Save the bounding box
        self.manual_bbox = (x1_img, y1_img, x2_img, y2_img)
        
        self.status_label.config(text=f"Bounding box drawn: ({int(x1_img)}, {int(y1_img)}), ({int(x2_img)}, {int(y2_img)}). Press Enter to confirm or T to redraw.")
    
    def save_with_manual_bbox(self):
        """Saves the image with the manually drawn bounding box"""
        if not self.manual_bbox:
            self.status_label.config(text="Draw a bounding box first!")
            return
            
        # Filename without extension for label
        img_filename = self.image_files[self.current_index]
        base_name = os.path.splitext(img_filename)[0]
        
        # Copy image to output folder
        img_dest = os.path.join(self.output_img_folder, img_filename)
        try:
            shutil.copy2(self.current_img_path, img_dest)
        except Exception as e:
            print(f"Error copying image: {e}")
            self.status_label.config(text=f"Error: Could not copy image - {str(e)}")
            return
        
        # Create label file with manual bounding box
        label_path = os.path.join(self.output_label_folder, f"{base_name}.txt")
        
        # Get the image dimensions
        height, width = self.current_img.shape[:2]
        
        # Convert to YOLO format (x_center, y_center, width, height)
        x1, y1, x2, y2 = self.manual_bbox
        x_center = ((x1 + x2) / 2) / width
        y_center = ((y1 + y2) / 2) / height
        w = (x2 - x1) / width
        h = (y2 - y1) / height
        
        # Write to label file (class_id x_center y_center width height)
        with open(label_path, 'w') as f:
            f.write(f"0 {x_center} {y_center} {w} {h}")
        
        # Store action for undo
        was_moved = self.delete_mode_enabled
        self.store_action_for_undo('manual', img_filename, was_moved)
        
        # Move to DELETE folder if delete mode is enabled
        self.move_to_delete_if_enabled(img_filename)
        
        self.status_label.config(text=f"Image saved with manual bounding box: {img_filename}")
        
        # Reset drawing mode and go to next image
        self.drawing_mode = False
        self.manual_bbox = None
        self.next_image()

def main():
    # Start the application
    root = tk.Tk()
    app = YoloAnnotationApp(root, model_path, input_folder, output_img_folder, output_label_folder, delete_folder, enable_delete_mode)
    root.mainloop()

if __name__ == "__main__":
    main()
