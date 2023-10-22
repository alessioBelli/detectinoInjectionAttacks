import os
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import os
from glob import glob
from multiprocessing import cpu_count
import numpy as np
from PIL import Image
import prnu
import time
import matplotlib.pyplot as plt
import argparse
import sys

class FingerprintCreation:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title("Creation of the fingerprint")

        # Create a frame to contain the canvas, progress bar, and labels
        self.frame = tk.Frame(window)
        self.frame.grid(row=0, column=0, padx=10, pady=10)

        self.video_source = 1
        self.vid = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width_true)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height_true)

        # Create canvas
        self.canvas = tk.Canvas(self.frame, width=640, height=360)
        self.canvas.pack()

        # Create frame for progress bar and labels
        self.progress_frame = tk.Frame(self.frame)
        self.progress_frame.pack(pady=10)

        self.display_resolution = (640, 360)
        self.analysis_thread = None
        self.frame_count = 0
        self.frame_n = 0

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack()

        self.percentage_label = tk.Label(self.progress_frame, text="0%")
        self.percentage_label.pack()

        self.text_label = tk.Label(self.progress_frame, text="")
        self.text_label.pack()
        self.check = False
        self.update()

    def update(self):
        #sleep to prevent lighting problems in the first frames
        if self.check == False:
            time.sleep(2)
            self.check = True

        ret, frame = self.vid.read()
        if ret:
            # resize only for visualisation purposes
            frame_re = cv2.resize(frame, self.display_resolution)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_re, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            
            if self.analysis_thread is None or not self.analysis_thread.is_alive():
                # 50 frames for the creation of the fingerprint
                if self.frame_count < 50:
                    # I take a frame every 10 frames
                    if self.frame_n % 10 == 0:
                        self.analysis_thread = threading.Thread(target=self.perform_analysis, args=(frame,))
                        self.analysis_thread.start()
                        self.frame_count += 1
                        self.progress_var.set(self.frame_count)
                        # Update percentage label 
                        self.update_percentage_label()  
                    self.frame_n +=1
                # when I have 50 frames I compute the fingerprint for the user
                else:
                    self.analysis_thread = threading.Thread(target=self.compute_prnu, args=())
                    self.analysis_thread.start()

        self.window.after(10, self.update)

    def update_percentage_label(self):
            percentage = (self.frame_count / 100) * 100
            self.percentage_label.config(text=f"{int(percentage)}%")
    
    def perform_analysis(self, frame):
        # save the current frame inside the output_put jpeg quality 100
        output_dir = "frames"
        os.makedirs(output_dir, exist_ok=True)
        frame_filename = os.path.join(output_dir, f"{self.frame_count}.jpg")
        cv2.imwrite(frame_filename, frame, params=[cv2.IMWRITE_JPEG_QUALITY, 100])

    def compute_prnu(self):
        # the resolution of the patch is the one passed as argument in the terminal
        cut = (patch_height, patch_width, 3)
        ff_dirlist = np.array(sorted(glob('frames/*')))
        imgs = []
        for img_path in (ff_dirlist):
            im = Image.open(img_path)
            im_arr = np.asarray(im)
            if im_arr.dtype != np.uint8:
                print('Error while reading image: {}'.format(img_path))
                continue
            if im_arr.ndim != 3:
                print('Image is not RGB: {}'.format(img_path))
                continue
            im_cut = prnu.cut_ctr(im_arr, cut)
            imgs += [im_cut]
        k = [prnu.extract_multiple_aligned(imgs, processes=cpu_count())]
        
        # compute the fingerprint and save inside the directory 'fingerprints'. Change the name of the fingerprint
        np.save("./fingerprints/acer.npy", k)
        self.progress_var.set(100)  # Update progress bar
        self.frame_count = 100
        self.update_percentage_label()  # Update percentage label
        self.vid.release()
        self.canvas.destroy()
        self.text_label.config(text="Fingerprint calculated!\nYou can now close this windows")
        

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

class TestWindow:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title("Testing")

        self.video_source = 1
        self.vid = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width_true)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height_true)

        # resolution only for visualisation purposes
        self.display_resolution = (640, 360)

        self.canvas_width = 640
        self.canvas_height = 480

        self.style = ttk.Style()
        self.style.configure('Custom.TButton', padding=10, relief="flat", background="#4CAF50", foreground="black")


        self.camera1_button = ttk.Button(window, text="Client camera", command=self.switch_to_camera1, style='Custom.TButton')
        self.camera2_button = ttk.Button(window, text="Attacker camera", command=self.switch_to_camera2, style='Custom.TButton')

        self.camera1_button.grid(row=0, column=1, padx=10, pady=10)
        self.camera2_button.grid(row=0, column=0, padx=10, pady=10)

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height)
        self.text_label = tk.Label(window, text="Checking...", padx=10, pady=10)

        self.canvas.grid(row=1, column=0, columnspan=2)
        self.text_label.grid(row=2, column=0, columnspan=2)

        self.analysis_thread = None

        self.frame_count = 0

        self.update()

    def switch_to_camera2(self):
        self.vid.release()  # Release the previous video source
        self.frame_count = 0
        self.video_source = 0  # Switch to camera 1
        self.text_label.config(text="Checking...")
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas_width = 640  # Set width for camera 1
        self.canvas_height = 480  # Set height for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width_false)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height_false)  # Set height for camera 1
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

    def switch_to_camera1(self):
        self.vid.release()  # Release the previous video source
        self.frame_count = 0
        self.video_source = 1  # Switch to camera 2 (modify to your specific source)
        self.text_label.config(text="Checking...")
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas_width = 640  # Set width for camera 2
        self.canvas_height = 480  # Set height for camera 2
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width_true)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height_true)  # Set height for camera 1
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            frame_re = cv2.resize(frame, self.display_resolution)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_re, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            # every 5th frame is analysed
            if self.frame_count % 5 == 0:
                if self.analysis_thread is None or not self.analysis_thread.is_alive():
                    self.analysis_thread = threading.Thread(target=self.perform_analysis, args=(frame,))
                    self.analysis_thread.start()
            self.frame_count +=1

        self.window.after(10, self.update)

    def perform_analysis(self, frame):
        # load the fingerprint correct of the user
        k = np.load("./fingerprints/acer.npy")
        k = np.stack(k, 0)

        w = prnu.extract_single(frame)

        cc2d = prnu.crosscorr_2d(k[0], w)
        
        prnu_pce = prnu.pce(cc2d)['pce']
        print(prnu_pce)
        if prnu_pce > 60:
            self.text_label.config(text="Webcam Authenticated", background="green")
        else:
            self.text_label.config(text="Webcam Not Authenticated", background="red")

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


class MainApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title("Source camera identification")

        # Set the window size
        window_width = 400
        window_height = 300
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Create a style for better appearance
        self.style = ttk.Style()
        self.style.configure('Custom.TButton', padding=10, relief="flat", background="#4CAF50", foreground="black")

        # Create a frame to hold the buttons and center it vertically
        button_frame = tk.Frame(window)
        button_frame.pack(expand=True, pady=(window_height // 3, window_height // 3))

        self.calculate_button = ttk.Button(button_frame, text="Calculate Fingerprint", command=self.open_fingerprint_creation, style='Custom.TButton')
        self.calculate_button.pack(pady=10)

        self.test_button = ttk.Button(button_frame, text="Test", command=self.test_function, style='Custom.TButton')
        self.test_button.pack()

        self.webcam_window = None  # Initialize the webcam window attribute

    

    def open_fingerprint_creation(self):
        if self.webcam_window is None:
            self.webcam_window = tk.Toplevel(self.window)
            self.webcam_app = FingerprintCreation(self.webcam_window, "Webcam App")

    def test_function(self):
        self.test_window = tk.Toplevel(self.window)
        self.test_app = TestWindow(self.test_window, "Test Window")


args = sys.argv
patch_width = int(args[1])
patch_height = int(args[2])
width_true = int(args[3])
height_true = int(args[4])
width_false = int(args[5])
height_false = int(args[6])


# Create the main Tkinter window and pass it to the MainApp class
root = tk.Tk()
app = MainApp(root, "Main App")
root.mainloop()
