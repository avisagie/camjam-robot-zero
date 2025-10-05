from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from gpiozero import CamJamKitRobot, DistanceSensor, Buzzer
import os
import threading
import time

DISTANCE_THRESHOLD = 15

class DistanceMonitor:
    def __init__(self, echo=18, trigger=17):
        self.sensor = DistanceSensor(echo=echo, trigger=trigger)
        self.distance = float('inf')
        self._running = False
        self._thread = None
        self._notifier = None
        
    def start(self):
        """Start the monitoring thread"""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.daemon = True
        self._thread.start()
        
    def stop(self):
        """Stop the monitoring thread"""
        self._running = False
        if self._thread:
            self._thread.join()
            
    def _monitor_loop(self):
        """Continuously monitor distance in background"""
        while self._running:
            try:
                self.distance = self.sensor.distance * 100  # Convert to cm
                if self.distance < 1.5*DISTANCE_THRESHOLD:
                    print(f'distance: {self.distance:.1f}')
                    if self._notifier is not None:
                        self._notifier()
                time.sleep(0.06)  # Prevent excessive CPU usage
            except Exception as e:
                print(f"Sensor error: {e}")
                time.sleep(1)  # Wait longer on error

    def get_distance(self):
        """Get the latest distance reading in cm"""
        return self.distance
    
    
    def set_notifier(self, fun):
        self._notifier = fun
        

from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

class RobotControlHandler(BaseHTTPRequestHandler):
    # Class variables to store robot and sensor instances
    robot = CamJamKitRobot()
    buzzer = Buzzer(4)
    distance_monitor = DistanceMonitor()
    distance_monitor.start()
    
    last_command = (0.0, 0.0)
    
    control_lock = threading.Lock()
    
    # Enable HTTP/1.1 protocol
    protocol_version = 'HTTP/1.1'
    
    def log_message(self, format, *args):
        """Override to add client address to log messages"""
        print(f"{self.client_address[0]} - {format%args}")
        

    def do_GET(self):
        if self.path == '/':
            self.path = '/joy.html'
            
        try:
            # Open the static file requested
            file_to_open = open(self.path[1:]).read()
            # Convert content to bytes once
            content = bytes(file_to_open, 'utf-8')
            
            self.send_response(200)
            
            # Set content type
            if self.path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif self.path.endswith('.js'):
                self.send_header('Content-type', 'application/javascript')
            elif self.path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            
            # Add content length header
            self.send_header('Content-Length', len(content))
            self.end_headers()
            
            # Send the file content
            self.wfile.write(content)
            
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes('File not found', 'utf-8'))
            

    def do_POST(self):
        if self.path == '/shutdown':
            print('Shutdown request received')

            # Stop robot and cleanup
            self.robot.stop()
            self.distance_monitor.stop()

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            response = bytes(json.dumps({'status': 'shutting down'}), 'utf-8')
            self.send_header('Content-Length', len(response))
            self.end_headers()
            self.wfile.write(response)

            # Wait before shutting down
            print('Shutting down in 0.5 seconds...')
            time.sleep(0.5)

            # Shutdown the system
            import subprocess
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])

        elif self.path == '/control':
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read and parse the POST data
            post_data = self.rfile.read(content_length)
            motor_speeds = json.loads(post_data.decode('utf-8'))
            
            # Extract motor values (-1023 to 1023)
            left = motor_speeds.get('left', 0)
            right = motor_speeds.get('right', 0)
            
            # Convert to motor values (-1 to 1)
            left = max(-1, min(1, left / 1023))
            right = max(-1, min(1, right / 1023))
            
            # Get current distance
            distance = self.distance_monitor.get_distance()
            # print(f'Distance: {distance:.1f}cm, Motors: {left:.2f}:{right:.2f}')
            
            # Control motors with safety check
            with self.control_lock:
                RobotControlHandler.last_command = (left, right)
                self.control_motors(left, right, distance)
            
            # Prepare response JSON
            response = {
                'status': 'ok',
                'distance': round(distance, 1)
            }
            content = bytes(json.dumps(response), 'utf-8')
            
            # Send response with distance info
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            

    @classmethod
    def trigger_control(cls):
        """class method update based on events such as distance"""
        with cls.control_lock:        
            left, right = cls.last_command
            distance = cls.distance_monitor.get_distance()
            
            cls.control_motors(left, right, distance)


    @classmethod
    def control_motors(cls, left, right, distance):
        """Control the robot motors with safety features and turning in place support."""

        print(f'tiggering motor control with {left} {right} {distance}')
            
        if left < -0.01 and right < -0.01:
            cls.buzzer.on()
        else:
            cls.buzzer.off()

        # Stop if values are close to zero
        if abs(left) < 0.1 and abs(right) < 0.1:
            cls.robot.stop()
            return
            
        # Prevent forward motion if too close to obstacle
        if distance < DISTANCE_THRESHOLD:  # Less than 10cm
            left = min(0, left)
            right = min(0, right)

        # Set motor speeds
        cls.robot.value = (left, right)
        print(f"Final motor values: {left:.2f}:{right:.2f}")
    
    
RobotControlHandler.distance_monitor.set_notifier(RobotControlHandler.trigger_control)
    
        
def run(handler_class=RobotControlHandler, port=8000):
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, handler_class)
    print(f'running in {os.getcwd()}')
    print(f'Starting threaded server on port {port}...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        handler_class.robot.stop()
        handler_class.distance_monitor.stop()
        httpd.server_close()

if __name__ == '__main__':
    run()