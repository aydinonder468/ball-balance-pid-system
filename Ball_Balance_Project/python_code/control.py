import cv2
import numpy as np
import serial
import time
from collections import deque


PORT = 'COM3'   
BAUD = 115200
CAM_W, CAM_H = 640, 480 
HISTORY_LEN = 300 


FIXED_CENTER_X = 104
FIXED_CENTER_Y = 83


MOVE_RANGE = 25




LIMIT_X_MIN = FIXED_CENTER_X - MOVE_RANGE
LIMIT_X_MAX = FIXED_CENTER_X + MOVE_RANGE
LIMIT_Y_MIN = FIXED_CENTER_Y - MOVE_RANGE
LIMIT_Y_MAX = FIXED_CENTER_Y + MOVE_RANGE



DIR_X = 1   
DIR_Y = -1  


LOWER_COLOR = np.array([40, 70, 70])
UPPER_COLOR = np.array([80, 255, 255])


history_ball_x = deque(maxlen=HISTORY_LEN)
history_ball_y = deque(maxlen=HISTORY_LEN)
history_error = deque(maxlen=HISTORY_LEN)

def nothing(x): pass


ser = None
try:
    ser = serial.Serial(PORT, BAUD, timeout=0)
    time.sleep(2)
    print(f"Sistem Hazir: {PORT}")
    print(f"Merkezler Ayarlandi -> X:{FIXED_CENTER_X}, Y:{FIXED_CENTER_Y}")
except:
    print("HATA: Arduino yok, simulasyon modu.")


WINDOW_NAME = "Fixed Center PID System"
cv2.namedWindow(WINDOW_NAME)
cv2.resizeWindow(WINDOW_NAME, 1000, 600)


cv2.createTrackbar("Kp", WINDOW_NAME, 35, 200, nothing) 
cv2.createTrackbar("Ki", WINDOW_NAME, 1, 100, nothing)  
cv2.createTrackbar("Kd", WINDOW_NAME, 30, 200, nothing) 

cap = cv2.VideoCapture(1) 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

p_err_x, p_err_y = 0, 0
int_x, int_y = 0, 0
prev_time = time.time()

def create_telemetry_panel(err_x_list, total_err_list):
    h = CAM_H
    panel = np.zeros((h, 300, 3), dtype=np.uint8)
    cv2.line(panel, (0, h//2), (300, h//2), (50, 50, 50), 1)

    def plot(data, color, offset_y, scale, label):
        cv2.putText(panel, label, (10, offset_y - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        if len(data) > 2:
            pts = list(data)
            for i in range(1, len(pts)):
                y1 = int(offset_y - (pts[i-1] * scale))
                y2 = int(offset_y - (pts[i] * scale))
                y1 = np.clip(y1, offset_y-90, offset_y+90)
                y2 = np.clip(y2, offset_y-90, offset_y+90)
                cv2.line(panel, (i-1, y1), (i, y2), color, 1)

    plot(err_x_list, (0, 255, 0), h//4, 0.5, "Pozisyon Hatasi (X)")
    plot(total_err_list, (0, 100, 255), 3*h//4, 0.5, "Toplam Hata")
    return panel

try:
    while True:
        ret, frame = cap.read()
        if not ret: break

        now = time.time()
        dt = now - prev_time
        prev_time = now
        if dt <= 0: dt = 0.01

        kp = cv2.getTrackbarPos("Kp", WINDOW_NAME) / 100.0
        ki = cv2.getTrackbarPos("Ki", WINDOW_NAME) / 1000.0
        kd = cv2.getTrackbarPos("Kd", WINDOW_NAME) / 100.0

        
        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5,5), 0), cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_COLOR, UPPER_COLOR)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        ball_detected = False
        center_screen_x = CAM_W // 2
        center_screen_y = CAM_H // 2

        if cnts:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            
            if r > 10:
                ball_detected = True
                err_x = center_screen_x - x
                err_y = y - center_screen_y 
                
                history_ball_x.append(err_x)
                history_error.append(np.sqrt(err_x**2 + err_y**2))

                # PID 
                int_x = np.clip(int_x + (err_x * dt), -300, 300)
                int_y = np.clip(int_y + (err_y * dt), -300, 300)
                
                pid_x = (kp * err_x) + (ki * int_x) + (kd * (err_x - p_err_x) / dt)
                pid_y = (kp * err_y) + (ki * int_y) + (kd * (err_y - p_err_y) / dt)
                p_err_x, p_err_y = err_x, err_y

                
                out_x = FIXED_CENTER_X + (pid_x * DIR_X)
                out_y = FIXED_CENTER_Y + (pid_y * DIR_Y)
                
            
                out_x = int(np.clip(out_x, LIMIT_X_MIN, LIMIT_X_MAX))
                out_y = int(np.clip(out_y, LIMIT_Y_MIN, LIMIT_Y_MAX))
                
                if ser: ser.write(f"X{out_x}Y{out_y}\n".encode())

                
                cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
                cv2.line(frame, (int(x), int(y)), (center_screen_x, center_screen_y), (0, 255, 0), 2)

        
        if not ball_detected:
            p_err_x, p_err_y = 0, 0
            int_x, int_y = 0, 0
            history_error.append(0)
          

        
        telemetry_panel = create_telemetry_panel(history_ball_x, history_error)
        if frame.shape[0] != telemetry_panel.shape[0]:
            telemetry_panel = cv2.resize(telemetry_panel, (300, frame.shape[0]))
        combined_view = np.hstack((frame, telemetry_panel))
        
        cv2.putText(combined_view, f"FIXED CENTER: X={FIXED_CENTER_X}, Y={FIXED_CENTER_Y}", 
                    (10, CAM_H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        cv2.imshow(WINDOW_NAME, combined_view)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

except Exception as e:
    print(f"Hata: {e}")
finally:
    if ser: ser.close()
    cap.release()
    cv2.destroyAllWindows()