import cv2
import mediapipe as mp
import playsound
import math

cap = cv2.VideoCapture(0)

mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils

reqd_nodes = [
    'LEFT_EYE',
    'RIGHT_EYE',
    'NOSE',
    'RIGHT_SHOULDER',
    'LEFT_SHOULDER'
]

# Initial posture data (dictionary to store all landmark coordinates)
initial_pose = None

def calculate_normalized_variation(initial_value, current_value, image_dimension):
    """Calculates normalized variation between initial and current values."""
    print(image_dimension)
    ch=int(current_value - initial_value)
    print(ch/image_dimension)
    return abs(ch/image_dimension)

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    init_results = pose.process(imgRGB)

    if init_results.pose_landmarks:
        mpDraw.draw_landmarks(img, init_results.pose_landmarks, mpPose.POSE_CONNECTIONS)

        
        
    cv2.imshow("Image", img)
    
    if cv2.waitKey(1) == ord('q'):
        # Capture initial pose on first detection
        if initial_pose is None:
            initial_pose = {}
            for idx, landmark in enumerate(init_results.pose_landmarks.landmark):
                landmark_name = mpPose.PoseLandmark(idx).name  # Use index for name
                if landmark_name in reqd_nodes:
                    initial_pose[landmark_name] = (landmark.x * img.shape[1], landmark.y * img.shape[0],landmark.z)
            print("Initial posture captured!")
        break

cap.release()
cv2.destroyAllWindows()

print(initial_pose)



cap = cv2.VideoCapture(0)


while True:
    success, img = cap.read()
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


        # Capture initial pose on first detection
        if initial_pose is None:
            initial_pose = {}
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmark_name = mpPose.PoseLandmark(idx).name  # Use index for name
                initial_pose[landmark_name] = (landmark.x * img.shape[1], landmark.y * img.shape[0], landmark.z)
            print("Initial posture captured!")

        # Check for variations from initial pose (normalized)
        threshold = 0.075  # You can adjust this threshold value (0-1)
        for landmark_name, (x, y, z) in initial_pose.items():
            if landmark_name in reqd_nodes:
                current_landmark = results.pose_landmarks.landmark[mpPose.PoseLandmark[landmark_name]]
                current_x, current_y, current_z = int(current_landmark.x * img.shape[1]), int(current_landmark.y * img.shape[0]), current_landmark.z
                variation_x = calculate_normalized_variation(x, current_x, img.shape[1])
                variation_y = calculate_normalized_variation(y, current_y, img.shape[0])
                variation_z = calculate_normalized_variation(z, current_z, 1)  # Normalize by 1 for z-axis (no image dimension)
                # You can implement logic based on variations in x, y, and z

                if variation_x > threshold or variation_y > threshold or variation_z > int(threshold/10):
                    playsound.playsound("beep-02.wav", False)
                    break  # Only beep once per frame

    cv2.imshow("Image", img)
    # Space to capture initial posture, q to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):
        if results.pose_landmarks:
            initial_pose = {}
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmark_name = mpPose.PoseLandmark(idx).name  # Use index for name
                initial_pose[landmark_name] = (landmark.x, landmark.y)
            print("Initial posture captured!")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
