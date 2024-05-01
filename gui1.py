import cv2
import mediapipe as mp
import playsound
import math
import tkinter as tk
from PIL import Image, ImageTk




mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils

global reqd_nodes
reqd_nodes = [
    'LEFT_EYE',
    'RIGHT_EYE',
    'NOSE',
    'RIGHT_SHOULDER',
    'LEFT_SHOULDER'
]
# Initial posture data (dictionary to store all landmark coordinates)
global initial_pose
initial_pose = None

global success, img
success = None
img = None

global init_results
init_results = None
global results
results = None

global tracking
tracking = False

global threshold
threshold = 0.075



# Create a window
root = tk.Tk()




def calculate_normalized_variation(initial_value, current_value, image_dimension):
    """Calculates normalized variation between initial and current values."""
    print(image_dimension)
    ch=int(current_value - initial_value)
    print(ch/image_dimension)
    return abs(ch/image_dimension)


def update():
    global success, img, init_results, results, tracking, initial_pose, reqd_nodes, threshold
    success, img = cap.read()

    if success:

        if tracking:
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = pose.process(imgRGB)
            if results.pose_landmarks:
                mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
                mpDraw.draw_landmarks(
                    image=img, 
                    landmark_list=init_results.pose_landmarks, 
                    connections=mpPose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mpDraw.DrawingSpec(color=(0, 245, 0))
                    )
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            imgPIL = Image.fromarray(imgRGB)
            imgTK = ImageTk.PhotoImage(image=imgPIL)
            live_feed.imgtk = imgTK
            live_feed.configure(image=imgTK)

            # Check for variations from initial pose (normalized)
            # threshold = 0.075  # You can adjust this threshold value (0-1)
            for landmark_name, (x, y, z) in initial_pose.items():
                if landmark_name in reqd_nodes:
                    current_landmark = results.pose_landmarks.landmark[mpPose.PoseLandmark[landmark_name]]
                    current_x, current_y, current_z = int(current_landmark.x * img.shape[1]), int(current_landmark.y * img.shape[0]), current_landmark.z
                    variation_x = calculate_normalized_variation(x, current_x, img.shape[1])
                    variation_y = calculate_normalized_variation(y, current_y, img.shape[0])
                    variation_z = calculate_normalized_variation(z, current_z, 1)  # Normalize by 1 for z-axis (no image dimension)
                    # You can implement logic based on variations in x, y, and z

                    # update posture_info label to show that the posture is ok with default font size and color
                    posture_info.config(text="Posture ok!", font=("Helvetica", 12), fg="black")

                    if variation_x > threshold or variation_y > threshold or variation_z > int(threshold/10):
                        # update posture_info label to show that the posture is not ok with red enlarged text
                        posture_info.config(text="Posture not ok!", font=("Helvetica", 20), fg="red")
                        playsound.playsound("beep-02.wav", False)
                        break  # Only beep once per frame
        else:
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            init_results = pose.process(imgRGB)
            if init_results.pose_landmarks:
                mpDraw.draw_landmarks(img, init_results.pose_landmarks, mpPose.POSE_CONNECTIONS)
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            imgPIL = Image.fromarray(imgRGB)
            imgTK = ImageTk.PhotoImage(image=imgPIL)
            live_feed.imgtk = imgTK
            live_feed.configure(image=imgTK)

    live_feed.after(10, update)


def initialize_posture():
    global initial_pose
    if initial_pose is None:
            initial_pose = {}
            for idx, landmark in enumerate(init_results.pose_landmarks.landmark):
                landmark_name = mpPose.PoseLandmark(idx).name  # Use index for name
                if landmark_name in reqd_nodes:
                    initial_pose[landmark_name] = (landmark.x * img.shape[1], landmark.y * img.shape[0],landmark.z)
            print("Initial posture captured!")


def start_tracking():
    # disable the button once it is pressed
    initialize_posture()

    global success, img, init_results, tracking, initial_pose
    # imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # results = pose.process(imgRGB)
    # print(results)

    tracking = True
    
    print("funciton triggered")
    # live_feed.after(10, start_tracking)


def user_settings():
    global threshold

    # open a new window with a text box to enter the treshold value
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("500x150")

    treshold_info_label = tk.Label(settings_window, text="Ideal treshold value is 0.09 . More the value, more permissible range motion.")
    treshold_info_label.pack()

    threshold_entry_label = tk.Label(settings_window, text="Threshold (0-1):")
    threshold_entry_label.pack()

    threshold_entry = tk.Entry(settings_window)
    threshold_entry.pack()

    def save_settings():
        global threshold
        threshold = float(threshold_entry.get())
        # update the threshold label in the main window
        threshold_label.config(text=f"Threshold: {threshold}")
        settings_window.destroy()
    
    save_button = tk.Button(settings_window, text="Save", command=save_settings)
    save_button.pack()


def reset_system():
    global tracking, initial_pose
    tracking = False
    initial_pose = None
    posture_info.config(text="")
    print("System reset!")


live_feed = tk.Label(root)
live_feed.pack()


start_button = tk.Button(root, text="Start", command=start_tracking)
start_button.pack()

settings_button = tk.Button(root, text="Settings", command=user_settings)
settings_button.pack()

# a label that will show the current threshold value which will be updated when the user changes the value
threshold_label = tk.Label(root, text=f"Threshold: {threshold}")
threshold_label.pack()

reset_button = tk.Button(root, text="Reset", command=reset_system)
reset_button.pack()

posture_info = tk.Label(root, text="")
posture_info.pack()



cap = cv2.VideoCapture(0)


# Trigger the update function
update()

# Start the GUI
root.mainloop()

# Release the capture and destroy the windows when the GUI is closed
cap.release()
cv2.destroyAllWindows()