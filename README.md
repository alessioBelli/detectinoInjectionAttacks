# Detection Injection Attacks in a Video Conference scenario

# Installation 🔧
In order to run the application, you need to install Python on your PC with several libraries. For facilitate this operation the file *requirements.txt* is provided.

After downloading the zip file from Github and unzipping it, to install the libraries you just need to execute on your terminal the `pip install -r requirements.txt` command in the path of the unzipped folder.

# Usage 🚨

`python app.py 1280 720 1280 720 640 380`, in which the argument are:
1. Width of the patch image used for the creation of the fingperprint
2. Height of the patch image used for the creation of the fingperprint
3. Width of the resolution of the user's webcam
4. Height of the resolution of the user's webcam
5. Width of the resolution of the attacker's webcam
6. Height of the resolution of the attacker's webcam
