import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
import os
import pandas as pd
from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
import io


class CaseLabelingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Case Labeling Tool")
        self.root.geometry("1200x900")

        # State variables
        self.cases_dir = None
        self.output_dir = None
        self.case_folders = []
        self.current_index = 0
        self.labeling_log = []
        self.labeled_configs = {}  # Store configs by label

        # Required files
        self.required_files = ['front_on.png', 'top_down.png', 'vectors_points.xlsx',
                               'Wing Config.csv', 'mode.txt']

        self.setup_ui()

    def setup_ui(self):
        # Top frame for directory selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Cases Directory:").grid(row=0, column=0, sticky=tk.W)
        self.cases_dir_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.cases_dir_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(top_frame, text="Browse", command=self.select_cases_dir).grid(row=0, column=2)

        ttk.Label(top_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(top_frame, text="Browse", command=self.select_output_dir).grid(row=1, column=2)

        ttk.Button(top_frame, text="Start Labeling", command=self.start_labeling).grid(row=2, column=1, pady=10)

        # Progress label
        self.progress_var = tk.StringVar(value="No cases loaded")
        ttk.Label(top_frame, textvariable=self.progress_var, font=('Arial', 12, 'bold')).grid(row=3, column=0,
                                                                                              columnspan=3)

        # Main content frame
        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Case name label
        self.case_name_var = tk.StringVar(value="")
        ttk.Label(content_frame, textvariable=self.case_name_var, font=('Arial', 16, 'bold')).pack()

        # Images frame
        images_frame = ttk.Frame(content_frame)
        images_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Front-on image
        self.front_label = ttk.Label(images_frame)
        self.front_label.pack(side=tk.LEFT, padx=10, expand=True)

        # Top-down image
        self.top_label = ttk.Label(images_frame)
        self.top_label.pack(side=tk.LEFT, padx=10, expand=True)

        # Buttons frame
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack(fill=tk.X)

        button_style = {'width': 15, 'padding': 10}
        ttk.Button(buttons_frame, text="Mixed", command=lambda: self.label_case("Mixed"), **button_style).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Torsion", command=lambda: self.label_case("Torsion"), **button_style).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Bending", command=lambda: self.label_case("Bending"), **button_style).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Corrupted", command=lambda: self.label_case("Corrupted"), **button_style).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Skip", command=self.skip_case, **button_style).pack(side=tk.LEFT, padx=5)

        # PDF generation frame
        pdf_frame = ttk.Frame(self.root, padding="10")
        pdf_frame.pack(fill=tk.X)

        ttk.Label(pdf_frame, text="Generate PDFs:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        ttk.Button(pdf_frame, text="Mixed PDF", command=lambda: self.generate_pdf("Mixed")).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_frame, text="Torsion PDF", command=lambda: self.generate_pdf("Torsion")).pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Button(pdf_frame, text="Bending PDF", command=lambda: self.generate_pdf("Bending")).pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Button(pdf_frame, text="Export Log", command=self.export_log).pack(side=tk.LEFT, padx=5)

    def select_cases_dir(self):
        directory = filedialog.askdirectory(title="Select Cases Directory")
        if directory:
            self.cases_dir_var.set(directory)
            self.cases_dir = directory

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            self.output_dir = directory

    def start_labeling(self):
        if not self.cases_dir or not self.output_dir:
            messagebox.showerror("Error", "Please select both Cases and Output directories")
            return

        # Get all case folders
        self.case_folders = [f for f in os.listdir(self.cases_dir)
                             if os.path.isdir(os.path.join(self.cases_dir, f))]
        self.case_folders.sort()

        if not self.case_folders:
            messagebox.showerror("Error", "No case folders found")
            return

        # Create output folders
        self.create_output_folders()

        # Reset state
        self.current_index = 0
        self.labeling_log = []
        self.labeled_configs = {"Mixed": [], "Torsion": [], "Bending": [], "Corrupted": [], "Duplicates": []}

        # Load first case
        self.load_case()

    def create_output_folders(self):
        folders = ["Mixed", "Torsion", "Bending", "Corrupted", "Duplicates"]
        for folder in folders:
            os.makedirs(os.path.join(self.output_dir, folder), exist_ok=True)

    def load_case(self):
        if self.current_index >= len(self.case_folders):
            messagebox.showinfo("Complete", f"All {len(self.case_folders)} cases have been processed!")
            self.save_log()
            return

        case_name = self.case_folders[self.current_index]
        case_path = os.path.join(self.cases_dir, case_name)

        # Update progress
        self.progress_var.set(f"Case {self.current_index + 1} of {len(self.case_folders)}")
        self.case_name_var.set(case_name)

        # Check if case is valid
        if not self.is_case_valid(case_path):
            self.auto_label_case("Corrupted")
            return

        # Check for duplicates
        if self.is_duplicate(case_path):
            self.auto_label_case("Duplicates")
            return

        # Load and display images
        self.display_images(case_path)

    def is_case_valid(self, case_path):
        for file in self.required_files:
            if not os.path.exists(os.path.join(case_path, file)):
                return False
        return True

    def is_duplicate(self, case_path):
        # Extract design number from folder name (Design_x_Mode_y)
        case_name = os.path.basename(case_path)
        try:
            design_num = case_name.split('_')[1]  # Get the x from Design_x_Mode_y
        except:
            return False

        config_path = os.path.join(case_path, 'Wing Config.csv')
        try:
            current_config = pd.read_csv(config_path, sep=',', decimal=',')
            current_config_str = current_config.to_json()

            # Check against all labeled configs with DIFFERENT design numbers
            for label, configs in self.labeled_configs.items():
                if label == "Duplicates":
                    continue
                for stored_design, stored_config in configs:
                    # Only duplicate if config matches AND design number is different
                    if stored_design != design_num and stored_config == current_config_str:
                        return True
        except Exception as e:
            print(f"Error checking duplicate: {e}")

        return False

    def display_images(self, case_path):
        try:
            # Load front_on image
            front_path = os.path.join(case_path, 'front_on.png')
            front_img = Image.open(front_path)
            front_img.thumbnail((500, 500))
            front_photo = ImageTk.PhotoImage(front_img)
            self.front_label.configure(image=front_photo)
            self.front_label.image = front_photo

            # Load top_down image
            top_path = os.path.join(case_path, 'top_down.png')
            top_img = Image.open(top_path)
            top_img.thumbnail((500, 500))
            top_photo = ImageTk.PhotoImage(top_img)
            self.top_label.configure(image=top_photo)
            self.top_label.image = top_photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load images: {e}")

    def label_case(self, label):
        case_name = self.case_folders[self.current_index]
        case_path = os.path.join(self.cases_dir, case_name)
        dest_path = os.path.join(self.output_dir, label, case_name)

        try:
            # Copy folder
            shutil.copytree(case_path, dest_path, dirs_exist_ok=True)

            # Store config with design number
            try:
                design_num = case_name.split('_')[1]
            except:
                design_num = case_name

            config_path = os.path.join(case_path, 'Wing Config.csv')
            config = pd.read_csv(config_path, sep=',', decimal=',')
            self.labeled_configs[label].append((design_num, config.to_json()))

            # Log the action
            self.labeling_log.append({
                'case': case_name,
                'label': label,
                'destination': dest_path
            })

            # Move to next case
            self.current_index += 1
            self.load_case()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy case: {e}")

    def auto_label_case(self, label):
        """Automatically label a case without user interaction"""
        case_name = self.case_folders[self.current_index]
        case_path = os.path.join(self.cases_dir, case_name)
        dest_path = os.path.join(self.output_dir, label, case_name)

        try:
            shutil.copytree(case_path, dest_path, dirs_exist_ok=True)

            self.labeling_log.append({
                'case': case_name,
                'label': label,
                'destination': dest_path,
                'auto': True
            })

            self.current_index += 1
            self.load_case()
        except Exception as e:
            print(f"Auto-label error: {e}")
            self.current_index += 1
            self.load_case()

    def skip_case(self):
        self.current_index += 1
        self.load_case()

    def generate_pdf(self, label):
        label_dir = os.path.join(self.output_dir, label)
        if not os.path.exists(label_dir):
            messagebox.showerror("Error", f"No {label} folder found")
            return

        cases = [f for f in os.listdir(label_dir) if os.path.isdir(os.path.join(label_dir, f))]

        if not cases:
            messagebox.showinfo("Info", f"No cases in {label} folder")
            return

        pdf_path = os.path.join(self.output_dir, f"{label}_report.pdf")

        try:
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4

            for case in cases:
                case_path = os.path.join(label_dir, case)

                # Case name (top left)
                c.setFont("Helvetica-Bold", 14)
                c.drawString(20 * mm, height - 20 * mm, case)

                # Mode content (top right)
                mode_path = os.path.join(case_path, 'mode.txt')
                if os.path.exists(mode_path):
                    with open(mode_path, 'r') as f:
                        mode_content = f.read().strip()
                    c.setFont("Helvetica", 10)
                    c.drawRightString(width - 20 * mm, height - 20 * mm, f"Mode: {mode_content}")

                # Vectors path
                vectors_path = os.path.join(label_dir, case, 'vectors_points.xlsx')
                c.setFont("Helvetica", 9)
                c.drawString(20 * mm, height - 35 * mm, f"Vectors: {vectors_path}")

                # Wing Config.csv content
                config_path = os.path.join(case_path, 'Wing Config.csv')
                if os.path.exists(config_path):
                    df = pd.read_csv(config_path, sep=',', decimal=',', header=None, names=['Parameter', 'Value'])
                    y_pos = height - 50 * mm
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(20 * mm, y_pos, "Wing Configuration:")
                    y_pos -= 6 * mm
                    c.setFont("Helvetica", 8)
                    for idx, row in df.iterrows():
                        param = str(row['Parameter'])
                        value = str(row['Value'])
                        c.drawString(25 * mm, y_pos, f"{param}: {value}")
                        y_pos -= 4 * mm
                        if y_pos < 100 * mm:
                            break

                # Images - vertically stacked with white background
                try:
                    # Front-on image (top)
                    front_path = os.path.join(case_path, 'front_on.png')
                    if os.path.exists(front_path):
                        # Open image and convert to RGB (removes transparency)
                        pil_img = Image.open(front_path)
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            # Create white background
                            background = Image.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            background.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                            pil_img = background

                        # Save to bytes for reportlab
                        img_buffer = io.BytesIO()
                        pil_img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img = ImageReader(img_buffer)
                        c.drawImage(img, 20 * mm, 135 * mm, width=170 * mm, height=60 * mm, preserveAspectRatio=True,
                                    mask='auto')

                    # Top-down image (bottom)
                    top_path = os.path.join(case_path, 'top_down.png')
                    if os.path.exists(top_path):
                        # Open image and convert to RGB (removes transparency)
                        pil_img = Image.open(top_path)
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            # Create white background
                            background = Image.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            background.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                            pil_img = background

                        # Save to bytes for reportlab
                        img_buffer = io.BytesIO()
                        pil_img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        img = ImageReader(img_buffer)
                        c.drawImage(img, 20 * mm, 65 * mm, width=170 * mm, height=60 * mm, preserveAspectRatio=True,
                                    mask='auto')
                except Exception as e:
                    print(f"Error adding images: {e}")

                c.showPage()

            c.save()
            messagebox.showinfo("Success", f"PDF generated: {pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

    def save_log(self):
        log_path = os.path.join(self.output_dir, 'labeling_log.json')
        with open(log_path, 'w') as f:
            json.dump(self.labeling_log, f, indent=2)

    def export_log(self):
        self.save_log()
        messagebox.showinfo("Success", f"Log exported to: {os.path.join(self.output_dir, 'labeling_log.json')}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CaseLabelingTool(root)
    root.mainloop()