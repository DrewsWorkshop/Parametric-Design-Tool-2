from direct.gui.DirectButton import DirectButton
from panda3d.core import LineSegs, NodePath


def _make_outline_geom(frame_size, color=(0, 0, 0, 1), thickness=2.0) -> NodePath:
	"""Create a rectangular outline geom matching a DirectGUI frameSize."""
	l, r, b, t = frame_size
	segs = LineSegs()
	segs.setThickness(thickness)
	segs.setColor(*color)
	segs.moveTo(l, 0, b)
	segs.drawTo(r, 0, b)
	segs.drawTo(r, 0, t)
	segs.drawTo(l, 0, t)
	segs.drawTo(l, 0, b)
	np = NodePath(segs.create())
	return np


def create_outline_button(text, pos=(0, 0, 0), scale=0.06, command=None, frame_size=(-0.25, 0.25, -0.08, 0.08),
                          color_ready=(0, 0, 0, 1), color_hover=(0.1, 0.1, 0.1, 1),
                          color_pressed=(0.2, 0.2, 0.2, 1), color_disabled=(0.5, 0.5, 0.5, 1),
                          thickness=2.0) -> DirectButton:
	"""Create a DirectButton with no fill (transparent) and only an outline."""
	geom_ready = _make_outline_geom(frame_size, color_ready, thickness)
	geom_hover = _make_outline_geom(frame_size, color_hover, thickness)
	geom_pressed = _make_outline_geom(frame_size, color_pressed, thickness)
	geom_disabled = _make_outline_geom(frame_size, color_disabled, thickness)
	btn = DirectButton(
		text=text,
		pos=pos,
		scale=scale,
		relief="flat",
		frameColor=(1, 1, 1, 0),  # transparent fill
		frameSize=frame_size,
		geom=(geom_ready, geom_pressed, geom_hover, geom_disabled),
		command=command,
	)
	return btn


