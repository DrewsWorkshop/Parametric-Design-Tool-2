from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from ExploreTab.Batch1 import run as run_batch1
from ExploreTab.Batch1Tournament import run as run_tournament
import os, json, shutil
 


class ExplorePanel:
    """Lightweight Explore tab container; keeps Explore UI isolated here."""

    def __init__(self):
        # Root frame for Explore UI; hidden by default
        self.root = DirectFrame(
            pos=(0, 0, 0),
            frameColor=(1, 1, 1, 0),  # transparent
            frameSize=(-1.6, 1.6, -0.95, 0.95),
            relief='flat',
        )
        self.root.hide()

        # Prompt shown when Explore opens
        self.body = OnscreenText(
            text="What object type do you want to explore?",
            pos=(0, 0.6),
            scale=0.045,
            fg=(0, 0, 0, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.body.reparentTo(self.root)

        # Simple object type buttons (minimal UI)
        self.btn_vase = DirectButton(
            text="Vase",
            pos=(0, 0, 0.45),
            scale=0.06,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief='flat',
            command=lambda: self._on_select_object("Vase"),
        )
        self.btn_vase.reparentTo(self.root)

        self.btn_table = DirectButton(
            text="Table",
            pos=(0, 0, 0.36),
            scale=0.06,
            frameColor=(0.6, 0.8, 0.6, 1),
            relief='flat',
            command=lambda: self._on_select_object("Table"),
        )
        self.btn_table.reparentTo(self.root)

        self.btn_stool = DirectButton(
            text="Stool",
            pos=(0, 0, 0.27),
            scale=0.06,
            frameColor=(0.8, 0.6, 0.6, 1),
            relief='flat',
            command=lambda: self._on_select_object("Stool"),
        )
        self.btn_stool.reparentTo(self.root)

        # Optional hooks for host app
        self._on_show_designs = None
        self._on_show_tournament = None

    def _on_select_object(self, object_type: str):
        # Run Batch1 then set up tournament pairs
        try:
            # Clear tmp folder on Explore selection
            try:
                tmp_dir = os.path.join("src", "ExploreTab", "tmp")
                for name in os.listdir(tmp_dir):
                    p = os.path.join(tmp_dir, name)
                    try:
                        if os.path.isfile(p) or os.path.islink(p):
                            os.remove(p)
                        elif os.path.isdir(p):
                            shutil.rmtree(p)
                    except Exception:
                        pass
            except Exception:
                pass
            # Reset tournament results file on Explore selection
            try:
                results_path = os.path.join("src", "ExploreTab", "tmp", "Batch1TournamentResults.txt")
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception:
                pass
            # Hide prompt and buttons after selection
            try:
                self.body.hide()
                self.btn_vase.hide()
                self.btn_table.hide()
                self.btn_stool.hide()
            except Exception:
                pass
            # Show Round 1 instructions overlay briefly, then proceed
            try:
                from direct.showbase.ShowBaseGlobal import base
                from direct.gui.DirectFrame import DirectFrame
                from direct.gui.OnscreenText import OnscreenText
                from panda3d.core import TextNode

                # Fullscreen transparent overlay (blocks clicks)
                self._instruction_overlay = DirectFrame(
                    pos=(0, 0, 0),
                    frameColor=(1, 1, 1, 0),
                    frameSize=(-1.6, 1.6, -0.95, 0.95),
                    relief='flat',
                )
                # Small white panel behind text
                self._instruction_panel = DirectFrame(
                    pos=(0, 0, 0),
                    frameColor=(1, 1, 1, 1),
                    frameSize=(-0.9, 0.9, -0.35, 0.35),
                    relief='flat',
                )
                self._instruction_panel.reparentTo(self._instruction_overlay)
                # Instruction text
                self._instruction_text = OnscreenText(
                    text="Round 1:\n\nYou’ll be shown a series of designs, please choose the one you prefer...",
                    pos=(0, 0.0),
                    scale=0.07,
                    fg=(0, 0, 0, 0),  # start transparent for fade-in
                    align=TextNode.ACenter,
                    mayChange=True,
                )
                self._instruction_text.reparentTo(self._instruction_panel)

                # Fade-in task for the instruction text (1 second)
                def _fade_in_task(task):
                    try:
                        duration = 1.0
                        t = min(1.0, task.time / duration)
                        # Set alpha from 0 -> 1 over duration
                        if hasattr(self, '_instruction_text') and self._instruction_text is not None:
                            self._instruction_text.setFg((0, 0, 0, t))
                        return task.done if t >= 1.0 else task.cont
                    except Exception:
                        return task.done

                base.taskMgr.add(_fade_in_task, "explore-instructions-fade")

                # After delay, fade out, then remove overlay and start generation
                def _start_after_delay(task):
                    try:
                        if hasattr(self, '_instruction_text') and self._instruction_text is not None:
                            self._instruction_text.hide()
                            self._instruction_text.destroy()
                            self._instruction_text = None
                        if hasattr(self, '_instruction_panel') and self._instruction_panel is not None:
                            self._instruction_panel.hide()
                            self._instruction_panel.destroy()
                            self._instruction_panel = None
                        if hasattr(self, '_instruction_overlay') and self._instruction_overlay is not None:
                            self._instruction_overlay.hide()
                            self._instruction_overlay.destroy()
                            self._instruction_overlay = None
                    except Exception:
                        pass
                    # Proceed with generation and tournament
                    try:
                        run_batch1(object_type)
                        run_tournament(object_type)
                        if callable(self._on_show_tournament):
                            self._on_show_tournament()
                    except Exception:
                        pass
                    return task.done

                # Fade-out task (1 second), then cleanup/proceed
                def _fade_out_start(task):
                    def _fade_out_task(tk):
                        try:
                            duration = 1.0
                            t = min(1.0, tk.time / duration)
                            a = max(0.0, 1.0 - t)  # 1 -> 0
                            if hasattr(self, '_instruction_text') and self._instruction_text is not None:
                                self._instruction_text.setFg((0, 0, 0, a))
                            return tk.done if t >= 1.0 else tk.cont
                        except Exception:
                            return tk.done
                    base.taskMgr.add(_fade_out_task, "explore-instructions-fade-out")
                    # Chain cleanup/start after fade-out finishes (~1s)
                    base.taskMgr.doMethodLater(1.05, _start_after_delay, "explore-instructions-cleanup")
                    return task.done

                # Show for 5 seconds, then start fade-out
                base.taskMgr.doMethodLater(5.0, _fade_out_start, "explore-instructions-delay")
            except Exception:
                # Fallback: if overlay fails, proceed immediately
                run_batch1(object_type)
                run_tournament(object_type)
                if callable(self._on_show_tournament):
                    self._on_show_tournament()
        except Exception as e:
            try:
                self.body.setText(f"Batch1 error: {e}")
                self.body.show()
            except Exception:
                pass

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()

    def set_hooks(self, on_show_designs=None, on_show_tournament=None):
        self._on_show_designs = on_show_designs
        self._on_show_tournament = on_show_tournament



