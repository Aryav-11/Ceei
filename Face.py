import face_recognition
import cv2
import subprocess
import os
from tkinter import messagebox, Tk
image = face_recognition.load_image_file("Imgs\\4.jpeg")
your_face_encoding = face_recognition.face_encodings(image)[0]
video_capture = cv2.VideoCapture(0)
video_capture.set(3, 640)  
video_capture.set(4, 480)  
frame_skip = 5
frame_counter = 0
face_recognized = False 
while not face_recognized:
    ret, frame = video_capture.read()
    frame_counter += 1
    if frame_counter % frame_skip != 0:
        continue
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    face_locations = face_recognition.face_locations(small_frame, model="hog")
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)
    if not face_encodings:
        print("No faces detected.")
        continue
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces([your_face_encoding], face_encoding)
        if True in matches:
            print("Face recognized! Access granted.")
            face_recognized = True
            break 
        else:
            print("Face not recognized.")
        top, right, bottom, left = [i * 4 for i in (top, right, bottom, left)]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    cv2.imshow("Video", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
video_capture.release()
cv2.destroyAllWindows()
if face_recognized:
    try:
        print("Running AI script in new Command Prompt window...")
        subprocess.Popen(['start', 'cmd', '/K', 'python main.py'], shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while running the AI script: {e}")
else:
    messagebox.showwarning("Access Denied", "Face not recognized. Access denied.")