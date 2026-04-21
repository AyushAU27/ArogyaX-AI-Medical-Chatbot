
# import cv2
# import numpy as np
# import time
# from scipy.signal import butter, filtfilt

# # -----------------------------
# # Safe Bandpass Filter
# # -----------------------------
# def bandpass_filter(signal, fs, low=0.7, high=3.0):
#     if fs <= 0 or len(signal) < 10:
#         return signal

#     nyquist = 0.5 * fs

#     low = low / nyquist
#     high = high / nyquist

#     # Clamp values (prevents crash)
#     low = max(0.001, low)
#     high = min(0.999, high)

#     if low >= high:
#         return signal

#     b, a = butter(2, [low, high], btype='band')
#     return filtfilt(b, a, signal)


# # -----------------------------
# # Robust BPM Calculation
# # -----------------------------
# def compute_bpm(signal, fs):
#     fft = np.fft.rfft(signal)
#     freqs = np.fft.rfftfreq(len(signal), d=1/fs)

#     # Only valid HR range (40–180 BPM)
#     mask = (freqs >= 0.7) & (freqs <= 3.0)

#     fft = np.abs(fft[mask])
#     freqs = freqs[mask]

#     if len(fft) == 0:
#         return 0

#     peak_freq = freqs[np.argmax(fft)]
#     bpm = peak_freq * 60

#     return bpm


# # -----------------------------
# # Face Detection (OpenCV)
# # -----------------------------
# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
# )

# cap = cv2.VideoCapture(0)

# signal_buffer = []
# timestamps = []
# bpm_history = []

# start_time = time.time()

# # -----------------------------
# # MAIN LOOP
# # -----------------------------
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#     for (x, y, w, h) in faces:

#         # 🔥 Forehead ROI (small + clean)
#         fx1 = x + int(w * 0.3)
#         fx2 = x + int(w * 0.7)
#         fy1 = y
#         fy2 = int(y + h * 0.2)

#         forehead = frame[fy1:fy2, fx1:fx2]

#         if forehead.size != 0:
#             green_mean = np.mean(forehead[:, :, 1])
#             signal_buffer.append(green_mean)
#             timestamps.append(time.time() - start_time)

#         cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)

#     # -----------------------------
#     # SIGNAL PROCESSING
#     # -----------------------------
#     if len(signal_buffer) > 400:
#         duration = timestamps[-1] - timestamps[0]

#         if duration > 0:
#             fs = len(signal_buffer) / duration

#             try:
#                 filtered = bandpass_filter(signal_buffer, fs)
#                 bpm = compute_bpm(filtered, fs)

#                 # ✅ Reject unrealistic jumps
#                 if 40 < bpm < 180:
#                     if len(bpm_history) == 0 or abs(bpm - bpm_history[-1]) < 15:
#                         bpm_history.append(bpm)

#                 # ✅ Strong smoothing (median)
#                 if len(bpm_history) > 15:
#                     bpm_history = bpm_history[-15:]

#                 if len(bpm_history) > 0:
#                     display_bpm = int(np.median(bpm_history))
#                 else:
#                     display_bpm = 0

#                 cv2.putText(frame, f"BPM: {display_bpm}", (20, 50),
#                             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

#             except Exception as e:
#                 print("Filter error:", e)

#         # Keep buffer fixed
#         signal_buffer = signal_buffer[-400:]
#         timestamps = timestamps[-400:]

#     cv2.imshow("rPPG Heart Rate (ESC to exit)", frame)

#     if cv2.waitKey(1) & 0xFF == 27:
#         break

# cap.release()
# cv2.destroyAllWindows()






# import cv2
# import numpy as np
# from scipy.signal import butter, lfilter
# import time

# # -----------------------------
# # Bandpass filter (heart rate range)
# # -----------------------------
# def bandpass_filter(signal, fs, low=0.7, high=4.0):
#     nyquist = 0.5 * fs
#     low /= nyquist
#     high /= nyquist
#     b, a = butter(1, [low, high], btype='band')
#     return lfilter(b, a, signal)

# # -----------------------------
# # Heart rate estimation (FFT)
# # -----------------------------
# def compute_bpm(signal, fs):
#     fft = np.fft.rfft(signal)
#     freqs = np.fft.rfftfreq(len(signal), d=1/fs)

#     idx = np.argmax(np.abs(fft))
#     freq = freqs[idx]

#     bpm = freq * 60
#     return bpm

# # -----------------------------
# # Load OpenCV face detector
# # -----------------------------
# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
# )

# # -----------------------------
# # Start webcam
# # -----------------------------
# cap = cv2.VideoCapture(0)

# signal_buffer = []
# timestamps = []

# start_time = time.time()

# # -----------------------------
# # Main loop
# # -----------------------------
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Convert to grayscale for detection
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#     # Detect face
#     faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#     for (x, y, w, h) in faces:
#         face_roi = frame[y:y+h, x:x+w]

#         if face_roi.size != 0:
#             # Extract green channel mean (rPPG signal)
#             green_mean = np.mean(face_roi[:, :, 1])
#             signal_buffer.append(green_mean)
#             timestamps.append(time.time() - start_time)

#         # Draw bounding box
#         cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

#     # -----------------------------
#     # Process signal after enough frames
#     # -----------------------------
#     if len(signal_buffer) > 150:
#         duration = timestamps[-1] - timestamps[0]

#         if duration > 0:
#             fs = len(signal_buffer) / duration

#             filtered = bandpass_filter(signal_buffer, fs)
#             bpm = compute_bpm(filtered, fs)

#             cv2.putText(frame, f"BPM: {int(bpm)}", (20, 50),
#                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

#         # Keep buffer size fixed
#         signal_buffer = signal_buffer[-150:]
#         timestamps = timestamps[-150:]

#     # Show output
#     cv2.imshow("rPPG Heart Rate (Press ESC to exit)", frame)

#     # Exit on ESC
#     if cv2.waitKey(1) & 0xFF == 27:
#         break

# # -----------------------------
# # Cleanup
# # -----------------------------
# cap.release()
# cv2.destroyAllWindows()


import cv2
import numpy as np
from scipy.signal import butter, filtfilt
import time

# -----------------------------
# Bandpass filter (better version)
# -----------------------------
def bandpass_filter(signal, fs, low=0.7, high=3.0):
    nyquist = 0.5 * fs
    low /= nyquist
    high /= nyquist
    b, a = butter(2, [low, high], btype='band')
    return filtfilt(b, a, signal)

# -----------------------------
# Heart rate estimation (robust)
# -----------------------------
def compute_bpm(signal, fs):
    fft = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=1/fs)

    # Keep only valid HR range (40–180 BPM)
    mask = (freqs >= 0.7) & (freqs <= 3.0)

    fft = np.abs(fft[mask])
    freqs = freqs[mask]

    if len(fft) == 0:
        return 0

    peak_freq = freqs[np.argmax(fft)]
    bpm = peak_freq * 60

    return bpm

# -----------------------------
# Face detection
# -----------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# -----------------------------
# Start webcam
# -----------------------------
cap = cv2.VideoCapture(0)

signal_buffer = []
timestamps = []
bpm_history = []

start_time = time.time()

# -----------------------------
# Main loop
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        # ✅ Use FOREHEAD only (better signal)
        fx1 = x
        fx2 = x + w
        fy1 = y
        fy2 = int(y + h * 0.3)

        forehead = frame[fy1:fy2, fx1:fx2]

        if forehead.size != 0:
            green_mean = np.mean(forehead[:, :, 1])
            signal_buffer.append(green_mean)
            timestamps.append(time.time() - start_time)

        # Draw box
        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)

    # -----------------------------
    # Process signal
    # -----------------------------
    if len(signal_buffer) > 300:
        duration = timestamps[-1] - timestamps[0]

        if duration > 0:
            fs = len(signal_buffer) / duration

            try:
                filtered = bandpass_filter(signal_buffer, fs)
                bpm = compute_bpm(filtered, fs)

                if 40 < bpm < 180:  # valid range
                    bpm_history.append(bpm)

                # Smooth output
                if len(bpm_history) > 10:
                    bpm_history = bpm_history[-10:]

                if len(bpm_history) > 0:
                    display_bpm = int(np.mean(bpm_history))
                else:
                    display_bpm = 0

                cv2.putText(frame, f"BPM: {display_bpm}", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            except:
                pass

        # Keep buffer manageable
        signal_buffer = signal_buffer[-300:]
        timestamps = timestamps[-300:]

    cv2.imshow("rPPG Heart Rate (ESC to exit)", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()