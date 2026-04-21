"""
Heart Rate Detection Module using rPPG
Integrates the rPPG detection script with FastAPI
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import subprocess
import threading
import time
import os
import signal

router = APIRouter(prefix="/heartrate", tags=["Heart Rate"])

# Global state for heart rate measurement
heartrate_process = None
heartrate_status = {
    "status": "idle",  # idle, measuring, completed
    "bpm": 0,
    "final_bpm": 0,
    "start_time": None
}
heartrate_lock = threading.Lock()

class HeartrateResponse(BaseModel):
    status: str
    message: str = None
    bpm: int = None
    final_bpm: int = None


def run_rppg_measurement():
    """
    Run the rPPG script in a separate process.
    This is a simplified version - in production, you'd want to:
    1. Capture the output from the rPPG script
    2. Parse BPM values in real-time
    3. Handle errors gracefully
    """
    global heartrate_process, heartrate_status
    
    try:
        with heartrate_lock:
            heartrate_status["status"] = "measuring"
            heartrate_status["start_time"] = time.time()
        
        # In a real implementation, you'd run the rPPG script and capture output
        # For now, we'll simulate the measurement process
        
        # Simulate measurement for 15 seconds
        for i in range(15):
            time.sleep(1)
            
            with heartrate_lock:
                if heartrate_status["status"] != "measuring":
                    break
                
                # Simulate BPM reading (in real implementation, parse from rPPG output)
                # This would come from the actual rPPG script output
                simulated_bpm = 72 + (i % 10) - 5  # Varies between 67-77
                heartrate_status["bpm"] = simulated_bpm
        
        # Measurement complete
        with heartrate_lock:
            if heartrate_status["status"] == "measuring":
                heartrate_status["status"] = "completed"
                heartrate_status["final_bpm"] = heartrate_status["bpm"]
                
    except Exception as e:
        print(f"rPPG measurement error: {e}")
        with heartrate_lock:
            heartrate_status["status"] = "error"


@router.post("/start")
async def start_heartrate(background_tasks: BackgroundTasks):
    """
    Start heart rate measurement using rPPG
    """
    global heartrate_process, heartrate_status
    
    with heartrate_lock:
        if heartrate_status["status"] == "measuring":
            return HeartrateResponse(
                status="already_running",
                message="Measurement already in progress"
            )
        
        # Reset status
        heartrate_status = {
            "status": "measuring",
            "bpm": 0,
            "final_bpm": 0,
            "start_time": time.time()
        }
    
    # Start measurement in background
    background_tasks.add_task(run_rppg_measurement)
    
    return HeartrateResponse(
        status="started",
        message="Heart rate measurement started"
    )


@router.get("/status")
async def get_heartrate_status():
    """
    Get current heart rate measurement status
    """
    with heartrate_lock:
        return HeartrateResponse(
            status=heartrate_status["status"],
            bpm=heartrate_status["bpm"] if heartrate_status["bpm"] > 0 else None,
            final_bpm=heartrate_status["final_bpm"] if heartrate_status["final_bpm"] > 0 else None
        )


@router.post("/stop")
async def stop_heartrate():
    """
    Stop heart rate measurement
    """
    global heartrate_process, heartrate_status
    
    with heartrate_lock:
        if heartrate_process:
            try:
                os.kill(heartrate_process.pid, signal.SIGTERM)
                heartrate_process = None
            except:
                pass
        
        was_measuring = heartrate_status["status"] == "measuring"
        heartrate_status["status"] = "idle"
        heartrate_status["bpm"] = 0
    
    return HeartrateResponse(
        status="stopped",
        message="Measurement stopped" if was_measuring else "No active measurement"
    )


# ============================================================
# INTEGRATION WITH ACTUAL rPPG SCRIPT
# ============================================================
# 
# To integrate the actual rppg.py script, you would:
#
# 1. Modify rppg.py to output BPM values to stdout or a file:
#    print(f"BPM:{bpm}", flush=True)
#
# 2. In run_rppg_measurement(), launch the script:
#    heartrate_process = subprocess.Popen(
#        ['python', 'rppg.py'],
#        stdout=subprocess.PIPE,
#        stderr=subprocess.PIPE,
#        universal_newlines=True
#    )
#
# 3. Read output in real-time:
#    for line in heartrate_process.stdout:
#        if line.startswith("BPM:"):
#            bpm = int(line.split(":")[1])
#            with heartrate_lock:
#                heartrate_status["bpm"] = bpm
#
# 4. Handle the OpenCV window in a way compatible with web deployment:
#    - Use a headless version
#    - Or stream video frames to frontend
#    - Or process pre-recorded video
#
# ============================================================
