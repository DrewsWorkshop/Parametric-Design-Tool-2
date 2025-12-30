from direct.task import Task
from panda3d.core import Vec3
import math


class OrbitCamera:
    """Orbit camera controller with drag-to-rotate and scroll-to-zoom."""
    
    def __init__(self, showbase, camera, mouse_watcher):
        self.showbase = showbase
        self.camera = camera
        self.mouse_watcher = mouse_watcher
        
        # Target (look-at) and spherical camera params
        self._target = Vec3(0, 0, 0)
        self._distance = 12.0         # zoom distance
        self._yaw = math.radians(-30)  # left/right
        self._pitch = math.radians(20)  # up/down (clamped)
        self._min_pitch = math.radians(-85)
        self._max_pitch = math.radians(85)
        self._min_dist = 3.0
        self._max_dist = 60.0

        # Drag state
        self._dragging = False
        self._last_mouse = None
        self._yaw_sensitivity = 1.5    # degrees per normalized-screen unit
        self._pitch_sensitivity = 1.2
        self._zoom_step = 1.1          # scroll multiplier

        # place camera initially
        self._update_camera()

        # mouse events
        self._register_events()

    def setup_task(self, task_mgr):
        """Setup the per-frame task to read mouse while dragging."""
        task_mgr.add(self._mouse_task, "orbit-mouse-task", sort=10)

    def _register_events(self):
        """Bind mouse events for orbit controls."""
        self.showbase.accept("mouse1", self._start_drag)
        self.showbase.accept("mouse1-up", self._end_drag)
        self.showbase.accept("wheel_up", self._zoom_in)
        self.showbase.accept("wheel_down", self._zoom_out)

    def _unregister_events(self):
        """Unbind mouse events to disable user input."""
        try:
            self.showbase.ignore("mouse1")
            self.showbase.ignore("mouse1-up")
            self.showbase.ignore("wheel_up")
            self.showbase.ignore("wheel_down")
        except Exception:
            pass

    def _start_drag(self):
        if self.mouse_watcher.hasMouse():
            m = self.mouse_watcher.getMouse()  # (-1..1, -1..1)
            self._last_mouse = (m.getX(), m.getY())
            self._dragging = True

    def _end_drag(self):
        self._dragging = False
        self._last_mouse = None

    def _zoom_in(self):
        self._distance = max(self._min_dist, self._distance / self._zoom_step)
        self._update_camera()

    def _zoom_out(self):
        self._distance = min(self._max_dist, self._distance * self._zoom_step)
        self._update_camera()

    def _mouse_task(self, task: Task):
        if self._dragging and self.mouse_watcher.hasMouse():
            m = self.mouse_watcher.getMouse()
            x, y = m.getX(), m.getY()
            if self._last_mouse is not None:
                dx = x - self._last_mouse[0]
                dy = y - self._last_mouse[1]
                # convert to radians; screen units are ~[-1,1]
                self._yaw   -= math.radians(dx * 180 * self._yaw_sensitivity)
                self._pitch -= math.radians(dy * 180 * self._pitch_sensitivity)
                # clamp pitch to avoid flipping
                self._pitch = max(self._min_pitch, min(self._max_pitch, self._pitch))
                self._update_camera()
            self._last_mouse = (x, y)
        return Task.cont

    def _update_camera(self):
        # spherical to cartesian around target
        r = self._distance
        cp = math.cos(self._pitch)
        x = r * cp * math.sin(self._yaw)
        y = -r * cp * math.cos(self._yaw)  # negative so yaw=0 looks toward -Y
        z = r * math.sin(self._pitch)

        self.camera.setPos(self._target + Vec3(x, y, z))
        self.camera.lookAt(self._target)

    def disable_controls(self):
        """Disable mouse controls for the camera."""
        self._dragging = False
        self._last_mouse = None
        self._unregister_events()

    def enable_controls(self):
        """Enable mouse controls for the camera."""
        # Controls are enabled by default, just ensure dragging is reset
        self._dragging = False
        self._last_mouse = None
        self._register_events()

    def set_target(self, target_pos):
        """Set a new target position for the camera to orbit around."""
        self._target = target_pos
        self._update_camera()

    def get_target(self):
        """Get the current target position."""
        return self._target

    def apply_config(self, config):
        """Apply camera configuration from object config."""
        self._distance = config["distance"]
        self._yaw = config["yaw"]
        self._pitch = config["pitch"]
        # Target is now set separately, not in config
        self._update_camera()