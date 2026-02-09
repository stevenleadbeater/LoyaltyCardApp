"""Tests for camera device enumeration and preference persistence."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from loyalty_card_app.camera_devices import (
    CameraInfo,
    enumerate_cameras,
    get_preferred_camera_node,
    select_camera,
    set_preferred_camera_node,
)


def _make_mock_device(display_name, props_dict=None):
    """Create a mock Gst.Device with the given display name and properties."""
    device = MagicMock()
    device.get_display_name.return_value = display_name

    if props_dict is not None:
        props = Gst.Structure.new_empty("properties")
        for key, val in props_dict.items():
            if isinstance(val, str):
                props.set_value(key, val)
            elif isinstance(val, int):
                props.set_value(key, val)
        device.get_properties.return_value = props
    else:
        device.get_properties.return_value = None

    device.create_element.return_value = MagicMock()
    return device


class TestCameraInfoFacingDetection(unittest.TestCase):
    """Tests for front/rear camera detection."""

    def test_libcamera_back_location(self):
        device = _make_mock_device(
            "Camera 0",
            {"api.libcamera.location": "back"},
        )
        info = CameraInfo(device)
        self.assertEqual(info.facing, "rear")

    def test_libcamera_front_location(self):
        device = _make_mock_device(
            "Camera 1",
            {"api.libcamera.location": "front"},
        )
        info = CameraInfo(device)
        self.assertEqual(info.facing, "front")

    def test_display_name_rear(self):
        device = _make_mock_device("Rear Camera", {})
        info = CameraInfo(device)
        self.assertEqual(info.facing, "rear")

    def test_display_name_front(self):
        device = _make_mock_device("Front Selfie Camera", {})
        info = CameraInfo(device)
        self.assertEqual(info.facing, "front")

    def test_display_name_back(self):
        device = _make_mock_device("Back Camera", {})
        info = CameraInfo(device)
        self.assertEqual(info.facing, "rear")

    def test_unknown_facing(self):
        device = _make_mock_device("USB Webcam", {})
        info = CameraInfo(device)
        self.assertEqual(info.facing, "unknown")

    def test_no_properties(self):
        device = _make_mock_device("Camera", None)
        info = CameraInfo(device)
        self.assertEqual(info.facing, "unknown")

    def test_node_description_rear(self):
        device = _make_mock_device(
            "Camera 0",
            {"node.description": "Rear Camera Module"},
        )
        info = CameraInfo(device)
        self.assertEqual(info.facing, "rear")


class TestCameraInfoNodePath(unittest.TestCase):
    """Tests for node path extraction."""

    def test_object_serial_string(self):
        device = _make_mock_device("Camera", {"object.serial": "42"})
        info = CameraInfo(device)
        self.assertEqual(info.node_path, "42")

    def test_object_path_string(self):
        device = _make_mock_device(
            "Camera",
            {"object.path": "api.libcamera:/dev/media0"},
        )
        info = CameraInfo(device)
        self.assertEqual(info.node_path, "api.libcamera:/dev/media0")

    def test_no_properties_returns_none(self):
        device = _make_mock_device("Camera", None)
        info = CameraInfo(device)
        self.assertIsNone(info.node_path)

    def test_empty_properties_returns_none(self):
        device = _make_mock_device("Camera", {})
        info = CameraInfo(device)
        self.assertIsNone(info.node_path)


class TestCameraInfoCreateSource(unittest.TestCase):
    """Tests for source element creation."""

    def test_create_source_delegates_to_device(self):
        device = _make_mock_device("Camera", {})
        info = CameraInfo(device)
        src = info.create_source("my-camera")
        device.create_element.assert_called_once_with("my-camera")

    def test_create_source_default_name(self):
        device = _make_mock_device("Camera", {})
        info = CameraInfo(device)
        src = info.create_source()
        device.create_element.assert_called_once_with("camera")


class TestSelectCamera(unittest.TestCase):
    """Tests for camera selection logic."""

    def test_empty_list(self):
        cam, idx = select_camera([])
        self.assertIsNone(cam)
        self.assertEqual(idx, -1)

    def test_single_camera(self):
        device = _make_mock_device("USB Webcam", {})
        cam_info = CameraInfo(device)
        with patch(
            "loyalty_card_app.camera_devices.get_preferred_camera_node",
            return_value=None,
        ):
            cam, idx = select_camera([cam_info])
        self.assertEqual(cam, cam_info)
        self.assertEqual(idx, 0)

    def test_prefers_rear_camera(self):
        front = CameraInfo(_make_mock_device("Front Camera", {}))
        rear = CameraInfo(
            _make_mock_device("Camera", {"api.libcamera.location": "back"})
        )
        with patch(
            "loyalty_card_app.camera_devices.get_preferred_camera_node",
            return_value=None,
        ):
            cam, idx = select_camera([front, rear])
        self.assertEqual(cam, rear)
        self.assertEqual(idx, 1)

    def test_prefers_saved_preference(self):
        cam0 = CameraInfo(
            _make_mock_device("Camera 0", {"object.serial": "10"})
        )
        cam1 = CameraInfo(
            _make_mock_device("Camera 1", {"object.serial": "20"})
        )
        with patch(
            "loyalty_card_app.camera_devices.get_preferred_camera_node",
            return_value="20",
        ):
            cam, idx = select_camera([cam0, cam1])
        self.assertEqual(cam, cam1)
        self.assertEqual(idx, 1)

    def test_saved_preference_missing_falls_to_rear(self):
        front = CameraInfo(_make_mock_device("Front Camera", {}))
        rear = CameraInfo(
            _make_mock_device("Camera", {"api.libcamera.location": "back"})
        )
        with patch(
            "loyalty_card_app.camera_devices.get_preferred_camera_node",
            return_value="999",
        ):
            cam, idx = select_camera([front, rear])
        self.assertEqual(cam, rear)
        self.assertEqual(idx, 1)


class TestPreferencePersistence(unittest.TestCase):
    """Tests for camera preference save/load."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "camera.json")

    def tearDown(self):
        if os.path.exists(self._config_path):
            os.unlink(self._config_path)
        os.rmdir(self._tmpdir)

    @patch("loyalty_card_app.camera_devices._get_config_path")
    def test_set_and_get(self, mock_path):
        mock_path.return_value = self._config_path
        set_preferred_camera_node("42")
        result = get_preferred_camera_node()
        self.assertEqual(result, "42")

    @patch("loyalty_card_app.camera_devices._get_config_path")
    def test_get_nonexistent(self, mock_path):
        mock_path.return_value = self._config_path
        result = get_preferred_camera_node()
        self.assertIsNone(result)

    @patch("loyalty_card_app.camera_devices._get_config_path")
    def test_overwrite_preference(self, mock_path):
        mock_path.return_value = self._config_path
        set_preferred_camera_node("10")
        set_preferred_camera_node("20")
        result = get_preferred_camera_node()
        self.assertEqual(result, "20")

    @patch("loyalty_card_app.camera_devices._get_config_path")
    def test_corrupt_json(self, mock_path):
        mock_path.return_value = self._config_path
        with open(self._config_path, "w") as f:
            f.write("not json{{{")
        result = get_preferred_camera_node()
        self.assertIsNone(result)


class TestCameraInfoRepr(unittest.TestCase):
    """Tests for CameraInfo string representation."""

    def test_repr_format(self):
        device = _make_mock_device(
            "Rear Camera",
            {"object.serial": "42", "api.libcamera.location": "back"},
        )
        info = CameraInfo(device)
        r = repr(info)
        self.assertIn("Rear Camera", r)
        self.assertIn("rear", r)
        self.assertIn("42", r)


if __name__ == "__main__":
    unittest.main()
