import json
import os
from datetime import datetime
import threading
import time


def get_default_param_configs():
	"""Return the default slider configurations.

	Each item is (name, (min, max), default).
	"""
	return [
		("Segment Count", (2, 9), 5),
		("Object Width", (0.5, 2.0), 1.0),
		("Twist Angle", (0, 45), 20),
		("Twist Groove Depth", (0, 5), 1),
		("Vertical Wave Frequency", (0, 20), 3),
		("Vertical Wave Depth", (0, 5), 1),
	]


def compute_page_size(range_vals):
	"""Compute page size (step) for a slider given (min, max)."""
	return (range_vals[1] - range_vals[0]) * 0.1


def format_slider_label_text(name, value):
	"""Format the label text for a slider value."""
	return f"{name}: {value:.1f}"


def get_all_parameters_from_sliders(sliders):
	"""Extract current parameter values from a dict of DirectSlider widgets."""
	return {name: slider["value"] for name, slider in sliders.items()}


def get_parameter_from_sliders(sliders, name, default=0.0):
	"""Get a single parameter value from sliders, with a default."""
	return sliders[name]["value"] if name in sliders else default


def save_favorite_to_file(file_path, parameters, object_type=None):
	"""Append a favorite entry to the JSON list file.

	Returns the total count after saving.
	"""
	entry = {
		"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		"parameters": parameters,
	}
	if object_type is not None:
		entry["object_type"] = object_type

	favorites = []
	if os.path.exists(file_path):
		try:
			with open(file_path, "r") as f:
				favorites = json.load(f)
		except (json.JSONDecodeError, FileNotFoundError):
			favorites = []

	favorites.append(entry)

	with open(file_path, "w") as f:
		json.dump(favorites, f, indent=2)

	return len(favorites)


def show_temporary_status(status_text_widget, message, color_rgba, duration_seconds):
	"""Set a status message with color for a limited time on a UI text widget."""
	status_text_widget.setText(message)
	status_text_widget.setFg(color_rgba)

	def _clear_after():
		time.sleep(duration_seconds)
		status_text_widget.setText("")

	threading.Thread(target=_clear_after, daemon=True).start()


