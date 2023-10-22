import os
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading

import os
from glob import glob
from multiprocessing import cpu_count, Pool

import numpy as np
from PIL import Image

import prnu

import cv2 as cv
import time

import sys
import matplotlib.pyplot as plt
from sklearn import metrics
import tqdm

class WebcamApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.video_source = 1  # Use the default webcam (you can change this to a video file path)
        self.vid = cv2.VideoCapture(self.video_source)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height for camera 1

        self.canvas = tk.Canvas(window, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack(side=tk.LEFT)

        self.canvas_width = 640  # Set width for camera 2
        self.canvas_height = 480  # Set height for camera 2

        


        self.analysis_thread = None  # Initialize the analysis thread attribute
        self.frame_count = 0  # Counter for frames
        self.frame_n = 0

        self.progress_var = tk.DoubleVar()  # Variable to track progress
        self.progress_bar = ttk.Progressbar(window, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack()

        self.percentage_label = tk.Label(window, text="0%")
        self.percentage_label.pack()

        self.update()

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

            
            if self.analysis_thread is None or not self.analysis_thread.is_alive():
                if self.frame_count < 50:
                    if self.frame_n % 5 == 0:
                        self.analysis_thread = threading.Thread(target=self.perform_analysis, args=(frame,))
                        self.analysis_thread.start()
                        self.frame_count += 1
                        self.progress_var.set(self.frame_count)  # Update progress bar
                        self.update_percentage_label()  # Update percentage label
                    self.frame_n +=1
                else:
                    self.analysis_thread = threading.Thread(target=self.compute_prnu, args=())
                    self.analysis_thread.start()

        self.window.after(10, self.update)

    def update_percentage_label(self):
            percentage = (self.frame_count / 100) * 100
            self.percentage_label.config(text=f"{int(percentage)}%")
    
    def perform_analysis(self, frame):
        # Save the frame to a directory
        output_dir = "frames"
        os.makedirs(output_dir, exist_ok=True)
        frame_filename = os.path.join(output_dir, f"{self.frame_count}.jpg")
        cv2.imwrite(frame_filename, frame, params=[cv2.IMWRITE_JPEG_QUALITY, 100])

    def compute_prnu(self):
        cut = (480, 640, 3)
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
        
        np.save("./acer.npy", k)
        print("END")
        self.progress_var.set(100)  # Update progress bar
        self.frame_count = 100
        self.update_percentage_label()  # Update percentage label
        self.vid.release()
        

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

class TestWindow:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.video_source = 1  # Default camera source
        self.vid = cv2.VideoCapture(self.video_source)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set height for camera 1

        self.display_resolution = (640, 480)

        self.canvas_width = 640  # Set a default width
        self.canvas_height = 480  # Set a default height

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(side=tk.LEFT)

        self.text_label = tk.Label(window, text="Checking...", padx=10, pady=10)
        self.text_label.pack(side=tk.RIGHT)

        self.camera1_button = tk.Button(window, text="Camera 1", command=self.switch_to_camera1)
        self.camera1_button.pack(side=tk.TOP)

        self.camera2_button = tk.Button(window, text="Camera 2", command=self.switch_to_camera2)
        self.camera2_button.pack(side=tk.TOP)

        self.analysis_thread = None  # Initialize the analysis thread attribute

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
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height for camera 1
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

    def switch_to_camera1(self):
        self.vid.release()  # Release the previous video source
        self.frame_count = 0
        self.video_source = 1  # Switch to camera 2 (modify to your specific source)
        self.text_label.config(text="Checking...")
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas_width = 640  # Set width for camera 2
        self.canvas_height = 480  # Set height for camera 2
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width for camera 1
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set height for camera 1
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            frame = cv2.resize(frame, self.display_resolution)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            if self.frame_count % 5 == 0:
                if self.analysis_thread is None or not self.analysis_thread.is_alive():
                    self.analysis_thread = threading.Thread(target=self.perform_analysis, args=(frame,))
                    self.analysis_thread.start()
            self.frame_count +=1

        self.window.after(10, self.update)

    def perform_analysis(self, frame):
        k = np.load("./acer.npy")
        frame_filename = os.path.join("./", "test.jpg")
        cv2.imwrite(frame_filename, frame, params=[cv2.IMWRITE_JPEG_QUALITY, 100])
        
        k = np.stack(k, 0)

        img = prnu.cut_ctr(np.asarray(Image.open("./test.jpg")), (480, 640, 3))
        w = prnu.extract_single(img)

        cc2d = prnu.crosscorr_2d(k[0], w)
        prnu_pce = prnu.pce(cc2d)['pce']
        print(prnu_pce)
        if prnu_pce > 28:
            self.text_label.config(text="Problema")
        else:
            self.text_label.config(text="Webcam Authenticated")

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

class MainApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.calculate_button = tk.Button(window, text="Calculate Fingerprint", command=self.open_webcam_app)
        self.calculate_button.pack()

        self.test_button = tk.Button(window, text="Test", command=self.test_function)
        self.test_button.pack()

        self.webcam_window = None  # Initialize the webcam window attribute

    def open_webcam_app(self):
        if self.webcam_window is None:
            self.webcam_window = tk.Toplevel(self.window)
            self.webcam_app = WebcamApp(self.webcam_window, "Webcam App")

    def test_function(self):
        self.test_window = tk.Toplevel(self.window)
        self.test_app = TestWindow(self.test_window, "Test Window")

# Create the main Tkinter window and pass it to the MainApp class
root = tk.Tk()
app = MainApp(root, "Main App")
root.mainloop()
