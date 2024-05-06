import cv2
import mediapipe as mp
import playsound
import math
import tkinter as tk
from PIL import Image, ImageTk
from plyer import notification
import datetime
import time
import threading


# initializing mediapose and drawing utilities
mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils


# global variables required                ##########################################################################################

global reqd_nodes
reqd_nodes = [
    'LEFT_EYE',
    'RIGHT_EYE',
    'NOSE',
    'RIGHT_SHOULDER',
    'LEFT_SHOULDER'
]

global success, img
success = None
img = None

global threshold
threshold = 0.075

global simple_live_feed_identifier
simple_live_feed_identifier = None

global live_feed_with_ideal_posture_identifier
live_feed_with_ideal_posture_identifier = None

global start_tracking_identifier
start_tracking_identifier = None

# Initial posture data (dictionary to store all landmark coordinates)
global initial_pose
initial_pose = None

global initial_results
initial_results = None

global bad_posture_alert, bad_posture_notification, last_notification_time
bad_posture_alert = True
bad_posture_notification = True
last_notification_time = datetime.datetime.now()

global timer_thread_var
timer_thread_var= None
global is_pomodoro_running
is_pomodoro_running = False


###############################################################################################################


# creating a window
root = tk.Tk()


# function to send wrong posture notification
def wrong_posture_notification():
    # send notification if the current time is 1 second more than the last notification time
    global last_notification_time
    current_time = datetime.datetime.now()
    if (current_time - last_notification_time).seconds >= 1:
        notification.notify(
            title="Posture Alert",
            message="Please correct your posture!",
            app_name="Posture Alert",
            timeout=10
        )
        last_notification_time = current_time


# function to calculate the normalized variation
def calculate_normalized_variation(initial_value, current_value, image_dimension):
    """Calculates normalized variation between initial and current values."""
    print(image_dimension)
    ch=int(current_value - initial_value)
    print(ch/image_dimension)
    return abs(ch/image_dimension)


# function to show the live feed
def simple_live_feed():
    global success, img
    global simple_live_feed_identifier

    success, img = cap.read()
    
    if success:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(imgRGB)
        if pose_results.pose_landmarks:
            mpDraw.draw_landmarks(img, pose_results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        imgPIL = Image.fromarray(imgRGB)
        imgTK = ImageTk.PhotoImage(image=imgPIL)
        live_feed.imgtk = imgTK
        live_feed.configure(image=imgTK)
    
    simple_live_feed_identifier = live_feed.after(10, simple_live_feed)


# function to show the live feed with ideal posture
def live_feed_with_ideal_posture():
    global initial_pose
    global initial_results
    global reqd_nodes
    global success, img
    global live_feed_with_ideal_posture_identifier

    success, img = cap.read()
    
    if success:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(imgRGB)
        if pose_results.pose_landmarks:
            mpDraw.draw_landmarks(img, pose_results.pose_landmarks, mpPose.POSE_CONNECTIONS)
            mpDraw.draw_landmarks(
                image=img,
                landmark_list=initial_results.pose_landmarks,
                connections=mpPose.POSE_CONNECTIONS,
                landmark_drawing_spec=mpDraw.DrawingSpec(color=(0, 245, 0))
            )
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            imgPIL = Image.fromarray(imgRGB)
            imgTK = ImageTk.PhotoImage(image=imgPIL)
            live_feed.imgtk = imgTK
            live_feed.configure(image=imgTK)
    
    live_feed_with_ideal_posture_identifier = live_feed.after(10, live_feed_with_ideal_posture)


# function to set the ideal posture
def set_ideal_posture():
    global initial_pose
    global initial_results
    global reqd_nodes
    global success, img
    global simple_live_feed_identifier
    global live_feed_with_ideal_posture_identifier

    initial_results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    if initial_results.pose_landmarks:

        if simple_live_feed_identifier: 
            live_feed.after_cancel(simple_live_feed_identifier)
            simple_live_feed_identifier = None
        
        if live_feed_with_ideal_posture_identifier:
            live_feed.after_cancel(live_feed_with_ideal_posture_identifier)
            live_feed_with_ideal_posture_identifier = None

        initial_pose = {}
        for idx, landmark in enumerate(initial_results.pose_landmarks.landmark):
            landmark_name = mpPose.PoseLandmark(idx).name
            if landmark_name in reqd_nodes:
                initial_pose[landmark_name] = (landmark.x * img.shape[1], landmark.y * img.shape[0], landmark.z)
            
        if initial_pose:
            start_button.config(state="normal")

        print("Initial posture captured!")
        live_feed_with_ideal_posture()


# function to start posture tracking
def start_tracking():
    global initial_pose
    global initial_results
    global reqd_nodes
    global success, img
    global simple_live_feed_identifier
    global live_feed_with_ideal_posture_identifier
    global threshold
    global start_tracking_identifier

    if simple_live_feed_identifier: 
        live_feed.after_cancel(simple_live_feed_identifier)
        simple_live_feed_identifier = None
        
    if live_feed_with_ideal_posture_identifier:
        live_feed.after_cancel(live_feed_with_ideal_posture_identifier)
        live_feed_with_ideal_posture_identifier = None
    
    set_posture_button.config(state="disabled")
    start_button.config(state="disabled")

    success, img = cap.read()
    
    if success:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(imgRGB)
        if pose_results.pose_landmarks:
            mpDraw.draw_landmarks(img, pose_results.pose_landmarks, mpPose.POSE_CONNECTIONS)
            mpDraw.draw_landmarks(
                image=img,
                landmark_list=initial_results.pose_landmarks,
                connections=mpPose.POSE_CONNECTIONS,
                landmark_drawing_spec=mpDraw.DrawingSpec(color=(0, 245, 0))
            )
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            imgPIL = Image.fromarray(imgRGB)
            imgTK = ImageTk.PhotoImage(image=imgPIL)
            live_feed.imgtk = imgTK
            live_feed.configure(image=imgTK)

            for landmark_name, (x, y, z) in initial_pose.items():
                if landmark_name in reqd_nodes:
                    current_landmark = pose_results.pose_landmarks.landmark[mpPose.PoseLandmark[landmark_name]]
                    current_x, current_y, current_z = int(current_landmark.x * img.shape[1]), int(current_landmark.y * img.shape[0]), current_landmark.z
                    variation_x = calculate_normalized_variation(x, current_x, img.shape[1])
                    variation_y = calculate_normalized_variation(y, current_y, img.shape[0])
                    variation_z = calculate_normalized_variation(z, current_z, 1)  # Normalize by 1 for z-axis (no image dimension)

                    # update posture_info label to show that the posture is ok with default font size and color
                    posture_info.config(text="Posture ok!", font=("Helvetica", 12), fg="black")

                    if variation_x > threshold or variation_y > threshold or variation_z > int(threshold/10):
                        # update posture_info label to show that the posture is not ok with red enlarged text
                        posture_info.config(text="Posture not ok!", font=("Helvetica", 20), fg="red")

                        if bad_posture_notification:
                            wrong_posture_notification()

                        if bad_posture_alert:
                            playsound.playsound("beep-02.wav", False)
                            break  # Only beep once per frame
    
    start_tracking_identifier = live_feed.after(10, start_tracking)


# user settings
def user_settings():
    global threshold
    global bad_posture_alert
    global bad_posture_notification
    
    # open a new window to enter treshold value
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")

    treshold_info_label = tk.Label(settings_window, text="Ideal treshold value is 0.09 . More the value, more permissible range motion.")
    treshold_info_label.pack()

    threshold_entry_label = tk.Label(settings_window, text="Threshold (0-1):")
    threshold_entry_label.pack()

    threshold_entry = tk.Entry(settings_window)
    threshold_entry.insert(0, threshold)
    threshold_entry.pack()

    # add a horizontal line
    tk.Label(settings_window, text="-------------------------------------------------------").pack()
    
    bad_posture_alert_var = tk.IntVar()
    bad_posture_alert_checkbox = tk.Checkbutton(settings_window, text="Bad posture beep alert", variable=bad_posture_alert_var)
    if bad_posture_alert:
        bad_posture_alert_checkbox.select()
    else:
        bad_posture_alert_checkbox.deselect()
    bad_posture_alert_checkbox.pack()

    bad_posture_notification_var = tk.IntVar()
    bad_posture_notification_checkbox = tk.Checkbutton(settings_window, text="Bad posture desktop notification", variable=bad_posture_notification_var)
    if bad_posture_notification:
        bad_posture_notification_checkbox.select()
    else:
        bad_posture_notification_checkbox.deselect()
    bad_posture_notification_checkbox.pack()

    tk.Label(settings_window, text="-------------------------------------------------------").pack()



    def save_settings():
        global threshold
        global bad_posture_alert
        global bad_posture_notification

        threshold = float(threshold_entry.get())
        # update the threshold label in the main window
        threshold_label.config(text=f"Threshold: {threshold}")

        if bad_posture_alert_var.get() == 1:
            bad_posture_alert = True
        else:
            bad_posture_alert = False

        if bad_posture_notification_var.get() == 1:
            bad_posture_notification = True
        else:
            bad_posture_notification = False

        settings_window.destroy()
    
    save_button = tk.Button(settings_window, text="Save", command=save_settings)
    save_button.pack()


# reset system
def reset_system():
    global initial_pose
    global initial_results
    global simple_live_feed_identifier
    global live_feed_with_ideal_posture_identifier
    global start_tracking_identifier

    if simple_live_feed_identifier:
        live_feed.after_cancel(simple_live_feed_identifier)
        simple_live_feed_identifier = None

    if live_feed_with_ideal_posture_identifier:
        live_feed.after_cancel(live_feed_with_ideal_posture_identifier)
        live_feed_with_ideal_posture_identifier = None

    if start_tracking_identifier:
        live_feed.after_cancel(start_tracking_identifier)
        start_tracking_identifier = None
    
    initial_pose = None
    initial_results = None

    start_button.config(state="disabled")
    set_posture_button.config(state="normal")
    posture_info.config(text="")

    simple_live_feed()

    print("System reset!")


# pomodoro feature implementation
def promodoro_feature():
    # create a new window for pomodoro feature
    pomodoro_window = tk.Toplevel(root)
    pomodoro_window.title("Pomodoro")

    # label with info "keep this window open for pomodoro feature"
    info_label = tk.Label(pomodoro_window, text="* Keep this window open for pomodoro feature")
    info_label.pack()

    # entry box to enter the time in minutes, also a label to show appropriate message
    time_entry_label = tk.Label(pomodoro_window, text="Enter time in minutes :")
    time_entry_label.pack()

    time_entry = tk.Entry(pomodoro_window)
    time_entry.insert(0, "25")
    time_entry.pack()

    break_time_label = tk.Label(pomodoro_window, text="Enter break duration in minutes :")
    break_time_label.pack()

    break_time_entry = tk.Entry(pomodoro_window)
    break_time_entry.insert(0, "5")
    break_time_entry.pack()

    # label to show the timer value using tkinter StringVar
    timer_var = tk.StringVar()
    timer_label = tk.Label(pomodoro_window, textvariable=timer_var)
    timer_label.config(font=("Helvetica", 20))
    timer_label.pack()

    # function to implement the timer
    def start_pomodoro(timer_var, time_entry_value):
        start_timer_button.config(state="disabled")
        time_entry.config(state="disabled")
        break_time_entry.config(state="disabled")
        global is_pomodoro_running
        is_pomodoro_running = True
        # implement the timer in a separate thread so that the GUI does not freeze
        def timer_thread(timer_var, time_entry_value):
            # get the time in seconds
            time_in_seconds = int(time_entry_value) * 60
            while time_in_seconds > 0 and is_pomodoro_running:
                min, secs = divmod(time_in_seconds, 60)
                timer_var.set(f"{min} : {secs}")
                time_in_seconds -= 1
                time.sleep(1)
            # show a notification when the timer is done
            if is_pomodoro_running:
                notification.notify(
                    title="Time to take a break!",
                    message="Time's up!",
                    app_name="Pomodoro",
                    timeout=10
                )
                playsound.playsound("beep-02.wav", False)
            break_time_in_seconds = 10
            if is_pomodoro_running:
                break_time_in_seconds = int(break_time_entry.get())*60
            while break_time_in_seconds > 0 and is_pomodoro_running:
                min, secs = divmod(break_time_in_seconds, 60)
                timer_var.set(f"Break: {min} : {secs}")
                break_time_in_seconds -= 1
                time.sleep(1)
            if is_pomodoro_running:
                notification.notify(
                    title="Break time over!",
                    message="Get back to work!",
                    app_name="Pomodoro",
                    timeout=10
                )
                playsound.playsound("beep-02.wav", False)
                timer_var.set("")
                timer_thread(timer_var, time_entry_value)

            

        # start the timer thread
        global timer_thread_var
        timer_thread_var = threading.Thread(target=timer_thread, args=(timer_var, time_entry_value))
        timer_thread_var.start()
            
    # start button to start the timer
    start_timer_button = tk.Button(pomodoro_window, text="Start Timer", command=lambda: start_pomodoro(timer_var, time_entry.get()))
    start_timer_button.pack()

    # reset button
    def reset_pomodoro():
        global timer_thread_var
        print(timer_thread_var)
        global is_pomodoro_running
        is_pomodoro_running = False
        if timer_thread_var:
            # timer_thread_var.terminate()
            timer_thread_var.join()
            timer_thread_var = None
        timer_var.set("")
        start_timer_button.config(state="normal")
        time_entry.config(state="normal")
        break_time_entry.config(state="normal")


    
    reset_timer_button = tk.Button(pomodoro_window, text="Reset", command=reset_pomodoro)
    reset_timer_button.pack()





# label to show the live feed
live_feed = tk.Label(root)
live_feed.pack()


# set posture button
set_posture_button = tk.Button(root, text="Set Posture", command=set_ideal_posture)
set_posture_button.pack()


# start button
start_button = tk.Button(root, text="Start", state="disabled", command=start_tracking)
start_button.pack()


# settings button
settings_button = tk.Button(root, text="Settings", command=user_settings)
settings_button.pack()


# treshold value label
threshold_label = tk.Label(root, text=f"Threshold: {threshold}")
threshold_label.pack()


# reset button
reset_button = tk.Button(root, text="Reset", command=reset_system)
reset_button.pack()


# posture info label
posture_info = tk.Label(root, text="")
posture_info.pack()


# pomodoro button
pomodoro_button = tk.Button(root, text="Pomodoro", command=promodoro_feature)
pomodoro_button.pack()


cap = cv2.VideoCapture(0)


# trigger the simple live feed function
simple_live_feed()


# start the GUI
root.mainloop()


# release the capture and destroy the windows when the GUI is closed
cap.release()
cv2.destroyAllWindows()