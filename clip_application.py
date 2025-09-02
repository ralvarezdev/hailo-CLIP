from time import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import hailo
from clip_app.clip_app_pipeline import ClipApp

class app_callback_class:
    def __init__(self):
        self.frame_count = 0
        self.use_frame = False
        self.running = True


    def increment(self):
        self.frame_count += 1

    def get_count(self):
        return self.frame_count

def app_callback(self, pad, info, user_data):
    """
    This is the callback function that will be called when data is available
    from the pipeline.
    Processing time should be kept to a minimum in this function.
    If longer processing is needed, consider using a separate thread / process.
    """
    # Initialize attributes if they don't exist
    if not hasattr(self, 'latest_detection'):
        self.latest_detection = None 
    if not hasattr(self, 'latest_detection_time'):
        self.latest_detection_time = None
    if not hasattr(self, 'timeout_seconds'):
        self.timeout_seconds = 0.25

    # Get current time
    now = time()

    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()

    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    if len(detections) == 0:
        detections = [roi] # Use the ROI as the detection

    found_label = False
    for detection in detections:
        classifications = detection.get_objects_typed(hailo.HAILO_CLASSIFICATION)
        if len(classifications) > 0:
            for classification in classifications:
                label = classification.get_label()
                if label != self.latest_detection:
                    confidence = classification.get_confidence()
                    print(f"{label} {confidence:.2f}", flush=True)
                    self.latest_detection = label
                self.latest_detection_time = now
                found_label = True

    # Check for timeout
    if not found_label and self.latest_detection is not None and self.latest_detection_time is not None:
        if now - self.latest_detection_time > self.timeout_seconds:
            print("None", flush=True)
            self.latest_detection = None
            self.latest_detection_time = None

    return Gst.PadProbeReturn.OK

def main():
    user_data = app_callback_class()
    clip = ClipApp(user_data, app_callback)
    clip.run()
    
if __name__ == "__main__":
    main()
