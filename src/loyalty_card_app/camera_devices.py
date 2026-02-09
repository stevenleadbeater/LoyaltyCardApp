"""Camera device enumeration and preference persistence.

Uses GStreamer DeviceMonitor to discover available cameras and
provides utilities for front/rear detection and preference storage.
"""

import json
import os

import gi

gi.require_version("Gst", "1.0")

from gi.repository import GLib, Gst


def _get_config_path():
    """Return path to the camera preference config file."""
    config_dir = GLib.get_user_config_dir()
    app_dir = os.path.join(config_dir, "loyalty-card-app")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "camera.json")


class CameraInfo:
    """Information about a discovered camera device."""

    def __init__(self, device):
        self.device = device
        self.display_name = device.get_display_name()
        props = device.get_properties()
        self.node_path = self._extract_node_path(props)
        self.facing = self._detect_facing(props, self.display_name)

    @staticmethod
    def _extract_node_path(props):
        """Extract an identifier usable as the pipewiresrc path property."""
        if props is None:
            return None
        # PipeWire object serial (most reliable identifier)
        val = props.get_string("object.serial")
        if val:
            return val
        ok, val = props.get_uint64("object.serial")
        if ok:
            return str(val)
        # PipeWire node ID
        ok, val = props.get_uint("node.id")
        if ok:
            return str(val)
        # Object path
        val = props.get_string("object.path")
        if val:
            return val
        return None

    @staticmethod
    def _detect_facing(props, display_name):
        """Detect whether this is a front or rear camera.

        Returns "front", "rear", or "unknown".
        """
        if props is not None:
            # libcamera exposes camera location directly
            val = props.get_string("api.libcamera.location")
            if val:
                lower = val.lower()
                if "front" in lower:
                    return "front"
                if "back" in lower or "rear" in lower:
                    return "rear"
            # Check node description from PipeWire properties
            desc = props.get_string("node.description")
            if desc:
                lower = desc.lower()
                if "front" in lower or "selfie" in lower:
                    return "front"
                if "rear" in lower or "back" in lower:
                    return "rear"
        # Fall back to checking the GStreamer display name
        if display_name:
            lower = display_name.lower()
            if "front" in lower or "selfie" in lower:
                return "front"
            if "rear" in lower or "back" in lower:
                return "rear"
        return "unknown"

    def create_source(self, name="camera"):
        """Create a GStreamer source element configured for this camera."""
        return self.device.create_element(name)

    def __repr__(self):
        return (
            f"CameraInfo({self.display_name!r}, "
            f"facing={self.facing!r}, path={self.node_path!r})"
        )


def enumerate_cameras():
    """Enumerate available camera devices.

    Returns a list of CameraInfo objects.
    """
    Gst.init(None)
    monitor = Gst.DeviceMonitor.new()
    monitor.add_filter("Video/Source", None)
    cameras = []
    if not monitor.start():
        return cameras
    for device in monitor.get_devices():
        cameras.append(CameraInfo(device))
    monitor.stop()
    return cameras


def get_preferred_camera_node():
    """Load the user's preferred camera node path from config."""
    try:
        with open(_get_config_path()) as f:
            data = json.load(f)
            return data.get("camera_node")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def set_preferred_camera_node(node_path):
    """Save the user's preferred camera node path to config."""
    config_path = _get_config_path()
    try:
        with open(config_path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}
    data["camera_node"] = node_path
    with open(config_path, "w") as f:
        json.dump(data, f)


def select_camera(cameras):
    """Select the best camera from the available list.

    Priority: saved preference > rear camera > first available.
    Returns (CameraInfo, index) or (None, -1) if no cameras.
    """
    if not cameras:
        return None, -1

    preferred = get_preferred_camera_node()
    if preferred:
        for i, cam in enumerate(cameras):
            if cam.node_path == preferred:
                return cam, i

    for i, cam in enumerate(cameras):
        if cam.facing == "rear":
            return cam, i

    return cameras[0], 0
