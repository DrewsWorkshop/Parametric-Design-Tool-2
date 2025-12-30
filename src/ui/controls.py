from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectFrame import DirectFrame
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from direct.gui import DirectGuiGlobals as DGG
 
import json
import os
from datetime import datetime
from utils.ui_utils import (
	get_default_param_configs,
	compute_page_size,
	format_slider_label_text,
	get_all_parameters_from_sliders,
	show_temporary_status,
)
from ui.favorites import save_favorite_to_file, FavoritesLabel
from ui.favorites_tab_utils import format_favorite_header, create_remove_button, create_edit_button, create_similar_designs_button, create_back_to_favorites_button, create_save_generated_design_button
from ExploreTab.explore_ui import ExplorePanel


class ParametricControls:
    """Comprehensive parametric controls for the modulated cylinder."""
    
    def __init__(self, on_parameter_change_callback, slider_config_func=None, on_object_change_callback=None, get_current_object_type_callable=None, on_hide_object_callback=None, on_show_object_callback=None, on_rebuild_with_params_callback=None, on_display_all_favorites_callback=None, on_clear_favorite_objects_callback=None, on_highlight_favorite_callback=None, on_slider_released_callback=None, on_display_round1_designs_callback=None):
        self.on_parameter_change = on_parameter_change_callback
        self.on_object_change = on_object_change_callback
        self.get_current_object_type = get_current_object_type_callable
        self.on_hide_object = on_hide_object_callback
        self.on_show_object = on_show_object_callback
        self.on_rebuild_with_params = on_rebuild_with_params_callback
        self.on_display_all_favorites = on_display_all_favorites_callback
        self.on_clear_favorite_objects = on_clear_favorite_objects_callback
        self.on_highlight_favorite = on_highlight_favorite_callback
        self.on_slider_released = on_slider_released_callback
        self.on_display_round1_designs = on_display_round1_designs_callback
        
        
        # Get slider configuration from the provided function or use default
        if slider_config_func:
            param_configs = slider_config_func()
        else:
            param_configs = get_default_param_configs()

        self.sliders = {}
        self.text_displays = {}
        self.slider_positions = {}  # Store fraction-based positions
        
        # Favorites state
        self.favorites_list = []
        self.current_favorite_index = 0

        # Generate positions for sliders (from top to bottom)
        for i, (name, range_vals, default) in enumerate(param_configs):
            # Calculate fraction-based positions: 15% from left, 15% from top with spacing
            x_fraction = 0.0  # 15% from left edge
            y_fraction = 0.85 - (i * 0.08)  # 15% from top (85% from bottom), 8% spacing
            
            # Store fraction positions for responsive updates
            self.slider_positions[name] = (x_fraction, y_fraction)
            
            # Convert to normalized coordinates
            pos = self.fraction_to_normalized(x_fraction, y_fraction)
            
            # Create slider
            slider = DirectSlider(
                range=range_vals, value=default, pageSize=compute_page_size(range_vals),
                orientation="horizontal",
                pos=pos, scale=0.4,
                thumb_frameColor=(0.6, 0.6, 0.8, 1),
                thumb_relief="flat",
                command=lambda n=name: self._on_slider_change(n)
            )
            self.sliders[name] = slider

            # Bind mouse button release to compute metrics once per adjustment
            try:
                slider.bind(DGG.B1RELEASE, lambda evt, n=name: self._on_slider_release(n))
                # Also bind the thumb, which often captures the drag/release events
                if hasattr(slider, 'thumb') and slider.thumb is not None:
                    slider.thumb.bind(DGG.B1RELEASE, lambda evt, n=name: self._on_slider_release(n))
            except Exception:
                pass

            # Create text display
            text = OnscreenText(
                text=format_slider_label_text(name, default),
                pos=(pos[0] - 0.4, pos[2] + 0.05), scale=0.03,
                fg=(0, 0, 0, 1), align=0, mayChange=True
            )
            self.text_displays[name] = text

        # Add Favorites button
        self.favorites_button = DirectButton(
            text="Favorites",
            pos=(-1.4, 0, .95), scale=0.04,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._open_favorites
        )

        # Add Builder button
        self.builder_button = DirectButton(
            text="Builder",
            pos=(-1.6, 0, .95), scale=0.04,
            frameColor=(0.8, 0.6, 0.2, 1),
            relief="flat",
            command=self._open_builder
        )

        # Add Explore button
        self.explore_button = DirectButton(
            text="Explore...",
            pos=(-1.2, 0, .95), scale=0.04,
            frameColor=(0.5, 0.8, 0.6, 1),
            relief="flat",
            command=self._open_explore
        )

        self.object_type_text = OnscreenText(
            text="Object Type:",
            pos=(-1.4, 0.85, 0), scale=0.04,
            fg=(0, 0, 0, 1), align=0, mayChange=True
        )

        # Add custom dropdown menu
        self.dropdown_items = ["Vase", "Table", "Stool"]
        self.dropdown_open = False
        self.selected_option = "Vase"
        
        # Main dropdown button
        self.dropdown_button = DirectButton(
            text=self.selected_option,
            pos=(-1.1, 0, 0.85), scale=0.04,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._toggle_dropdown
        )
        
        # Dropdown options frame (initially hidden)
        self.dropdown_frame = DirectFrame(
            pos=(-1.1, 0, 0.8), scale=0.04,
            frameColor=(0.4, 0.4, 0.6, 1),
            relief="flat"
        )
        self.dropdown_frame.hide()
        
        # Create option buttons with better spacing
        self.option_buttons = []
        for i, option in enumerate(self.dropdown_items):
            button = DirectButton(
                text=option,
                pos=(0, 0, -i * 1.25), scale=1.0,
                frameColor=(0.5, 0.5, 0.7, 1),
                relief="flat",
                command=self._select_option,
                extraArgs=[option]
            )
            button.reparentTo(self.dropdown_frame)
            self.option_buttons.append(button)

        # Status text for save confirmation
        self.status_text = OnscreenText(
            text="",
            pos=(0, -0.9), scale=0.03,
            fg=(0, 1, 0, 1), align=1, mayChange=True
        )

        # Builder mode label (bottom-center)
        self.builder_mode_text = OnscreenText(
            text="Height | Diameter",
            pos=(0, -0.80), scale=0.06,
            fg=(0, 0, 0, 1), align=TextNode.ACenter, mayChange=True
        )
        # Show by default on startup (builder mode)
        self.builder_mode_text.show()
        
        # New User button (top-right)
        self.new_user_button = DirectButton(
            text="New User? Click Here",
            pos=(1.1, 0, 0.9), scale=0.06,
            frameColor=(0.2, 0.6, 0.8, 1),
            text_fg=(1, 1, 1, 1),
            relief="flat",
            command=self._on_new_user_click
        )
        self.new_user_button.show()
        # Trash metric label (bottom-center, above status text)
        self.trash_metric_text = OnscreenText(
            text="Test Metric: --",
            pos=(0, -0.86), scale=0.05,
            fg=(0, 0, 0, 1), align=TextNode.ACenter, mayChange=True
        )
        self.trash_metric_text.show()

        # Info icon to the right of trash metric text (Builder tab)
        try:
            # Resolve image path robustly
            img_path = os.path.join("src", "ui", "ui_images", "info.png")
            if not os.path.exists(img_path):
                print(f"[UI] info.png not found at {img_path}")
            # Get position from trash text; handle (x, z) or (x, y, z)
            pos_val = self.trash_metric_text.getPos()
            try:
                # Try 3-component
                tx, ty, tz = pos_val
            except Exception:
                # Fallback for 2-component (x, z)
                tx, tz = pos_val
                ty = 0
            # Create icon as a DirectButton to ensure hover events work
            self.trash_info_icon = DirectButton(
                image=img_path,
                pos=(tx + 0.57, 0, tz + 0.01),
                scale=0.05,
                frameColor=(1, 1, 1, 0),  # invisible frame
                relief='flat',
                pressEffect=False,
            )
            # Match parent and layering
            self.trash_info_icon.reparentTo(self.trash_metric_text.getParent())
            self.trash_info_icon.setTransparency(TransparencyAttrib.MAlpha)
            self.trash_info_icon.setDepthTest(False)
            self.trash_info_icon.setDepthWrite(False)
            self.trash_info_icon.setBin('fixed', 100)
            self.trash_info_icon['state'] = DGG.NORMAL
            self.trash_info_icon.show()

            # Tooltip (hidden until hover)
            self.trash_info_tooltip = OnscreenText(
                text="Trash metric: estimated unusable waste",
                pos=(tx + 0.57, tz + 0.2),
                scale=0.04,
                fg=(0, 0, 0, 1),
                mayChange=True
            )
            self.trash_info_tooltip.reparentTo(self.trash_metric_text.getParent())
            self.trash_info_tooltip.hide()

            # Hover bindings
            try:
                self.trash_info_icon.bind(DGG.ENTER, lambda evt: self.trash_info_tooltip.show())
                self.trash_info_icon.bind(DGG.EXIT,  lambda evt: self.trash_info_tooltip.hide())
            except Exception:
                pass
        except Exception as e:
            print(f"[UI] Failed to create info icon: {e}")
            self.trash_info_icon = None
            self.trash_info_tooltip = None

        # Overhang warning text (persistent when overhang is detected)
        self.overhang_warning_text = OnscreenText(
            text="",
            pos=(0, -0.95), scale=0.04,
            fg=(1, 0, 0, 1), align=1, mayChange=True
        )
        self.overhang_warning_text.hide()

        # Add favorite label (after status_text is created)
        self.favorite_label = FavoritesLabel(
            save_callback=self._save_favorite,
            status_text=self.status_text
        )
        
        # Show the favorites button
        self.favorite_label.show()
        
        # Info panel to display favorites data (hidden; not used now)
        self.favorites_info_text = OnscreenText(
            text="",
            pos=(0, 0.6), scale=0.04,
            fg=(0, 0, 0, 1), align=1, mayChange=True
        )
        self.favorites_info_text.hide()

        # Header label for favorites: shows object type and rating
        self.favorites_header_text = OnscreenText(
            text="",
            pos=(0, 0.7), scale=0.075,
            fg=(0, 0, 0, 1), align=TextNode.ACenter, mayChange=True
        )
        self.favorites_header_text.hide()

        # Remove button for favorites tab
        self.favorites_remove_button = create_remove_button()
        # Wire removal handler
        self.favorites_remove_button['command'] = self._remove_current_favorite
        self.favorites_remove_button.hide()

        # Edit button for favorites tab (no-op for now)
        self.favorites_edit_button = create_edit_button()
        self.favorites_edit_button['command'] = self._edit_current_favorite
        self.favorites_edit_button.hide()

        # Similar designs button for favorites tab
        self.favorites_similar_button = create_similar_designs_button()
        self.favorites_similar_button['command'] = self._hide_similar_button
        self.favorites_similar_button.hide()

        # Back to favorites button
        self.back_to_favorites_button = create_back_to_favorites_button()
        self.back_to_favorites_button['command'] = self._show_favorites_buttons
        self.back_to_favorites_button.hide()

        # Save generated design button
        self.save_generated_design_button = create_save_generated_design_button()
        self.save_generated_design_button['command'] = self._save_generated_design
        self.save_generated_design_button.hide()
        

        # Favorites navigation arrows (hidden until Favorites opened)
        self.fav_prev_button = DirectButton(
            text="<",
            pos=(-1, 0, 0), scale=0.1,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._favorites_prev
        )
        self.fav_prev_button.hide()

        self.fav_next_button = DirectButton(
            text=">",
            pos=(1, 0, 0), scale=0.1,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._favorites_next
        )
        self.fav_next_button.hide()
        
        # Set up window resize event handler
        from direct.showbase.ShowBaseGlobal import base
        base.accept('window-resized', self.on_window_resize)

        # Explore panel (kept isolated in ExploreTab folder)
        self.explore_panel = ExplorePanel()
        self.explore_panel.hide()
        # Hook to start tournament display after Batch1/Tournament generation
        try:
            self.explore_panel.set_hooks(on_show_tournament=self._show_batch1_tournament)
        except Exception:
            pass

    def fraction_to_normalized(self, x_fraction, y_fraction):
        """Convert window fractions to normalized coordinates."""
        normalized_x = x_fraction * 2 - 1
        normalized_y = y_fraction * 2 - 1
        return normalized_x, 0, normalized_y

    def _show_batch1_tournament(self):
        """Ask the main app to display current tournament match."""
        try:
            from direct.showbase.ShowBaseGlobal import base
            if hasattr(base, 'start_batch1_tournament'):
                base.start_batch1_tournament()
        except Exception:
            pass

    def on_window_resize(self):
        """Reposition all sliders when window resizes."""
        # Keep info icon aligned with trash metric text
        try:
            if hasattr(self, 'trash_metric_text') and hasattr(self, 'trash_info_icon') and self.trash_info_icon is not None:
                pos_val = self.trash_metric_text.getPos()
                try:
                    tx, ty, tz = pos_val
                except Exception:
                    tx, tz = pos_val
                    ty = 0
                self.trash_info_icon.setPos(tx + 0.57, 0, tz + 0.15)
                if hasattr(self, 'trash_info_tooltip') and self.trash_info_tooltip is not None:
                    self.trash_info_tooltip.setPos(tx + 0.57, tz + 0.15)
        except Exception:
            pass
        for name, (x_fraction, y_fraction) in self.slider_positions.items():
            new_pos = self.fraction_to_normalized(x_fraction, y_fraction)
            
            # Update slider position
            if name in self.sliders:
                self.sliders[name].setPos(new_pos)
            
            # Update text position (maintain offset above slider)
            if name in self.text_displays:
                text_pos = (new_pos[0], new_pos[2] + 0.05)
                self.text_displays[name].setPos(text_pos)

    def _on_slider_change(self, slider_name):
        """Internal callback when any slider value changes."""
        value = self.sliders[slider_name]["value"]
        self.text_displays[slider_name].setText(format_slider_label_text(slider_name, value))
        
        if self.on_parameter_change:
            # Get all current parameter values
            params = self.get_all_parameters()
            self.on_parameter_change(params)

    def _on_slider_release(self, slider_name):
        """Mouse release handler to trigger metrics computation once per change."""
        if callable(getattr(self, 'on_slider_released', None)):
            try:
                self.on_slider_released()
            except Exception:
                pass

    def update_builder_label_text(self, text):
        """Update the bottom-center builder mode label text."""
        if hasattr(self, 'builder_mode_text'):
            self.builder_mode_text.setText(text)

    def update_trash_metric_text(self, text):
        """Update the trash metric label text."""
        if hasattr(self, 'trash_metric_text'):
            self.trash_metric_text.setText(text)

    def _save_favorite(self, rating=None):
        """Save current slider configuration to favorites file."""
        try:
            params = self.get_all_parameters()
            object_type = self.get_current_object_type() if callable(self.get_current_object_type) else None
            
            # Check for overhang before saving
            from geometry.vase.geometry import overhangVaseCheck
            has_overhang = overhangVaseCheck(
                segment_count=int(params.get("Segment Count", 5)),
                object_width=float(params.get("Object Width", 3.0)),
                twist_angle=float(params.get("Twist Angle", 20.0)),
                twist_groove_depth=float(params.get("Twist Groove Depth", 1.0)),
                vertical_wave_freq=int(params.get("Vertical Wave Frequency", 3)),
                vertical_wave_depth=float(params.get("Vertical Wave Depth", 1.0))
            )
            
            if has_overhang:
                show_temporary_status(self.status_text, "Cannot save: Object has overhang issues", (1, 0, 0, 1), 3)
                return
            
            total = save_favorite_to_file("src/tmp/favorites.txt", params, object_type=object_type, rating=rating)
            rating_text = f" with {rating}-star rating" if rating else ""
            show_temporary_status(self.status_text, f"Favorite saved{rating_text}! ({total} total)", (0, 1, 0, 1), 3)
        except Exception as e:
            show_temporary_status(self.status_text, f"Error saving: {str(e)}", (1, 0, 0, 1), 3)

    def _clear_alldesigns_file(self):
        """Clear AllDesigns.txt file for fresh exploration session."""
        try:
            import os
            import json
            
            # Path to AllDesigns.txt
            alldesigns_path = os.path.join("src", "ExploreTab", "Bayesian", "tmp_explore", "AllDesigns.txt")
            
            # Create empty file or clear existing file
            with open(alldesigns_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            
            
        except Exception as e:
            print(f"[ERROR] Failed to clear AllDesigns.txt: {e}")

    def _open_favorites(self):
        """Open favorites list (placeholder for now)."""
        print("Favorites button clicked!")
        show_temporary_status(self.status_text, "Favorites", (1, 1, 0, 1), 2)
        # Hide Builder Mode label when entering favorites
        self.builder_mode_text.hide()
        if hasattr(self, 'trash_metric_text'):
            self.trash_metric_text.hide()
        if hasattr(self, 'trash_info_icon') and self.trash_info_icon is not None:
            self.trash_info_icon.hide()
        
        # Hide New User button when entering favorites
        self.new_user_button.hide()
        
        # Hide Explore UI when switching to Favorites
        if hasattr(self, 'explore_panel'):
            self.explore_panel.hide()
        
        # Hide all sliders and their text displays
        for slider in self.sliders.values():
            slider.hide()
        for text in self.text_displays.values():
            text.hide()
        
        # Hide Object Type label and dropdown
        self.object_type_text.hide()
        self.dropdown_button.hide()
        self.dropdown_frame.hide()
        
        # Hide Save to Favorites label
        self.favorite_label.hide()
        
        # Hide overhang warning when switching to favorites
        self.hide_overhang_warning()
        
        # Hide the 3D object
        if callable(self.on_hide_object):
            self.on_hide_object()

        # Load favorites and display all at once
        try:
            self.favorites_list = []
            self.current_favorite_index = 0
            if os.path.exists("src/tmp/favorites.txt"):
                with open("src/tmp/favorites.txt", "r") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    self.favorites_list = loaded
            
            # Display all favorites at once
            if callable(self.on_display_all_favorites):
                self.on_display_all_favorites(self.favorites_list)
            
            # Highlight the first favorite if available
            if self.favorites_list:
                self._highlight_current_favorite()
                self._update_favorites_header()
        except Exception as e:
            show_temporary_status(self.status_text, f"Failed to load favorites: {e}", (1, 0, 0, 1), 3)
        
        # Show navigation arrows in Favorites view
        self.fav_prev_button.show()
        self.fav_next_button.show()
        # Hide header label (no longer showing rating)
        self.favorites_header_text.hide()
        # Show remove button
        self.favorites_remove_button.show()
        # Show edit button
        self.favorites_edit_button.show()
        # Show similar designs button only if there are favorites
        if len(self.favorites_list) > 0:
            self.favorites_similar_button.show()
        else:
            self.favorites_similar_button.hide()

    def _open_builder(self):
        """Open builder interface - restore all UI elements."""
        print("Builder button clicked!")
        show_temporary_status(self.status_text, "Builder mode", (1, 0.5, 0, 1), 2)
        # Show Builder Mode label in builder
        self.builder_mode_text.show()
        if hasattr(self, 'trash_metric_text'):
            self.trash_metric_text.show()
        if hasattr(self, 'trash_info_icon') and self.trash_info_icon is not None:
            self.trash_info_icon.show()
        
        # Show New User button in builder
        self.new_user_button.show()
        # Hide Explore UI when switching to Builder
        if hasattr(self, 'explore_panel'):
            self.explore_panel.hide()

    # Info icon/tooltip handlers removed
        
        # Show all sliders and their text displays
        for slider in self.sliders.values():
            slider.show()
        for text in self.text_displays.values():
            text.show()
        
        # Show Object Type label and dropdown
        self.object_type_text.show()
        self.dropdown_button.show()
        
        # Show Save to Favorites button
        self.favorite_label.show()
        
        # Show the 3D object
        if callable(self.on_show_object):
            self.on_show_object()

        # Hide favorites info panel and header
        self.favorites_info_text.hide()
        self.favorites_info_text.setText("")
        self.favorites_header_text.hide()
        self.favorites_header_text.setText("")
        # Hide remove button
        self.favorites_remove_button.hide()
        # Hide edit button
        self.favorites_edit_button.hide()
        # Hide similar designs button
        self.favorites_similar_button.hide()
        
        # Hide navigation arrows when leaving Favorites
        self.fav_prev_button.hide()
        self.fav_next_button.hide()
        
        # Clear favorite objects from scene
        if hasattr(self, 'on_clear_favorite_objects') and callable(self.on_clear_favorite_objects):
            self.on_clear_favorite_objects()
        
        # Apply camera configuration for current object type when returning to builder
        if callable(self.on_object_change):
            current_object = self.selected_option
            print(f"Applying camera config for current object: {current_object}")
            self.on_object_change(current_object)

    def _open_explore(self):
        """Open the Explore tab UI and hide builder/favorites controls."""
        try:
            # Clear AllDesigns.txt for fresh exploration session
            # Skip AllDesigns.txt clearing - not needed
			
            # Hide builder-specific elements
            self.builder_mode_text.hide()
            if hasattr(self, 'trash_metric_text'):
                self.trash_metric_text.hide()
            if hasattr(self, 'trash_info_icon') and self.trash_info_icon is not None:
                self.trash_info_icon.hide()
            
            # Hide New User button when entering explore
            self.new_user_button.hide()

            # Hide sliders and associated labels
            for slider in self.sliders.values():
                slider.hide()
            for text in self.text_displays.values():
                text.hide()

            # Hide object type controls and favorites UI scaffolding
            self.object_type_text.hide()
            self.dropdown_button.hide()
            self.dropdown_frame.hide()
            self.favorite_label.hide()
            self.favorites_info_text.hide()
            self.favorites_header_text.hide()
            self.favorites_remove_button.hide()
            self.favorites_edit_button.hide()
            self.favorites_similar_button.hide()
            self.fav_prev_button.hide()
            self.fav_next_button.hide()

            # Show Explore panel
            if hasattr(self, 'explore_panel'):
                self.explore_panel.show()

            # Hide 3D object while in Explore
            if callable(self.on_hide_object):
                self.on_hide_object()

            # Clear any favorites objects displayed in the scene
            if hasattr(self, 'on_clear_favorite_objects') and callable(self.on_clear_favorite_objects):
                self.on_clear_favorite_objects()
        except Exception:
            pass

    def _on_new_user_click(self):
        """Handle New User button click - clear favorites.txt for new user."""
        print("New User? Click Here button clicked!")
        self._clear_favorites_file()

    def _clear_favorites_file(self):
        """Clear the favorites.txt file for new user."""
        try:
            favorites_path = "src/tmp/favorites.txt"
            if os.path.exists(favorites_path):
                with open(favorites_path, 'w') as f:
                    f.write("")  # Clear the file
                print(f"Cleared favorites file: {favorites_path}")
                show_temporary_status(self.status_text, "Favorites cleared for new user!", (0, 0.8, 0, 1), 3)
            else:
                print(f"Favorites file not found: {favorites_path}")
                show_temporary_status(self.status_text, "No favorites to clear", (0.8, 0.8, 0, 1), 2)
        except Exception as e:
            print(f"Error clearing favorites file: {e}")
            show_temporary_status(self.status_text, "Error clearing favorites", (0.8, 0.2, 0, 1), 2)

    def _show_round1_designs(self):
        """Load Round1 designs from ExploreTab and display them in a grid."""
        try:
            import json, os
            base = os.path.join('src', 'ExploreTab', 'Bayesian')
            path = os.path.join(base, 'Designs.txt')
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                designs = json.load(f)
            # Prefer explore-specific display if available
            if callable(self.on_display_round1_designs):
                self.on_display_round1_designs(designs)
            elif callable(self.on_display_all_favorites):
                # Fallback: reuse favorites grid
                self.on_display_all_favorites(designs)
        except Exception:
            pass

    def _favorites_prev(self):
        if not self.favorites_list:
            show_temporary_status(self.status_text, "No favorites", (1, 1, 0, 1), 1)
            return
        self.current_favorite_index = (self.current_favorite_index - 1) % len(self.favorites_list)
        self._highlight_current_favorite()
        self._update_favorites_header()

    def _favorites_next(self):
        if not self.favorites_list:
            show_temporary_status(self.status_text, "No favorites", (1, 1, 0, 1), 1)
            return
        self.current_favorite_index = (self.current_favorite_index + 1) % len(self.favorites_list)
        self._highlight_current_favorite()
        self._update_favorites_header()

    def _highlight_current_favorite(self):
        """Highlight the currently selected favorite in the grid view."""
        if not self.favorites_list or not hasattr(self, 'on_highlight_favorite'):
            return
        
        # Call the main app to highlight the current favorite
        if callable(self.on_highlight_favorite):
            self.on_highlight_favorite(self.current_favorite_index)

    def _update_favorites_header(self):
        """Update header with current favorite's object type and rating."""
        if not self.favorites_list:
            self.favorites_header_text.setText("")
            self.favorites_edit_button.setText("Edit")
            return
        idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))
        entry = self.favorites_list[idx]
        self.favorites_header_text.setText(format_favorite_header(entry))
        
        # Update edit button text with object type
        object_type = entry.get("object_type", "Object")
        self.favorites_edit_button.setText(f"Edit {object_type}")

    def _load_current_favorite_object(self):
        """Load the current favorite's object onto the screen."""
        if not self.favorites_list or not callable(self.on_rebuild_with_params):
            return
        entry = self.favorites_list[self.current_favorite_index]
        params = entry.get("parameters", {})
        object_type = entry.get("object_type", None)
        self.on_rebuild_with_params(params, object_type)

    def _edit_current_favorite(self):
        """Open builder with the parameters of the currently viewed favorite."""
        try:
            if not self.favorites_list:
                show_temporary_status(self.status_text, "No favorites to edit", (1, 1, 0, 1), 2)
                return
            idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))
            entry = self.favorites_list[idx]
            params = entry.get("parameters", {})
            object_type = entry.get("object_type", None)

            # Switch to builder UI first
            self._open_builder()

            # Set dropdown selection to the object's type
            if object_type in ["Vase", "Table", "Stool"]:
                self.selected_option = object_type
                self.dropdown_button['text'] = object_type
                if callable(self.on_object_change):
                    # Apply camera config and defaults for object type
                    self.on_object_change(object_type)

            # Apply the favorite's parameters to the sliders
            for param_name, param_value in params.items():
                if param_name in self.sliders:
                    self.sliders[param_name]['value'] = param_value
                    # Update the text display
                    if param_name in self.text_displays:
                        self.text_displays[param_name].setText(
                            format_slider_label_text(param_name, param_value)
                        )

            # Trigger parameter change to rebuild with the favorite's parameters
            if self.on_parameter_change:
                self.on_parameter_change(params)

            show_temporary_status(self.status_text, "Loaded favorite into builder", (0, 1, 0, 1), 2)
        except Exception as e:
            show_temporary_status(self.status_text, f"Edit failed: {e}", (1, 0, 0, 1), 3)

    def _hide_similar_button(self):
        """Hide the similar designs button when clicked and run genetic algorithm."""
        self.favorites_similar_button.hide()
        self.favorites_edit_button.hide()
        self.favorites_remove_button.hide()
        self.back_to_favorites_button.show()
        
        # Clear the viewer of favorites designs
        self.favorites_list = []
        self.current_favorite_index = 0
        if callable(self.on_display_all_favorites):
            self.on_display_all_favorites([])  # Clear the display
        if callable(self.on_hide_object):
            self.on_hide_object()  # Hide any displayed object
        
        # Run genetic algorithm
        from GeneticAlgorithm.GA_proto import run_genetic_algorithm
        print("Running genetic algorithm...")
        result = run_genetic_algorithm("src/tmp/favorites.txt", "src/tmp/designsGA.txt", verbose=True)
        print(f"Genetic algorithm result: {result}")
        if result:
            # Run overhang optimization
            from ErrorCheck.overhang_opt import main as optimize_overhangs
            optimize_overhangs()
            
            # Load and display the generated designs
            self._load_generated_designs("src/tmp/designsGA.txt")
            show_temporary_status(self.status_text, "Generated similar designs!", (0, 1, 0, 1), 3)
        else:
            show_temporary_status(self.status_text, "No designs generated", (1, 1, 0, 1), 2)

    def _load_generated_designs(self, filename):
        """Load generated designs from GA file and display them."""
        try:
            with open(filename, 'r') as f:
                self.favorites_list = json.load(f)
            
            self.current_favorite_index = 0
            if callable(self.on_display_all_favorites):
                self.on_display_all_favorites(self.favorites_list)
            self._highlight_current_favorite()
            self._update_favorites_header()
            # Don't load individual object - just display the grid
            
            # Show the Save to Favorites button for generated designs
            self.save_generated_design_button.show()
            
        except Exception as e:
            show_temporary_status(self.status_text, f"Failed to load designs: {e}", (1, 0, 0, 1), 3)

    def _save_generated_design(self):
        """Save the currently viewed generated design to favorites."""
        try:
            if not self.favorites_list:
                show_temporary_status(self.status_text, "No design to save", (1, 1, 0, 1), 2)
                return
            
            idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))
            entry = self.favorites_list[idx]
            params = entry.get("parameters", {})
            object_type = entry.get("object_type", "Unknown")
            
            # Save to favorites with rating 5
            save_favorite_to_file("src/tmp/favorites.txt", params, object_type, 5)
            show_temporary_status(self.status_text, f"Saved {object_type} to favorites!", (0, 1, 0, 1), 2)
            
        except Exception as e:
            show_temporary_status(self.status_text, f"Failed to save: {e}", (1, 0, 0, 1), 3)

    def _show_favorites_buttons(self):
        """Show the favorites buttons when back is clicked."""
        self.back_to_favorites_button.hide()
        self.favorites_edit_button.show()
        self.favorites_remove_button.show()
        
        # Hide the Save to Favorites button when back to normal favorites
        self.save_generated_design_button.hide()
        
        # Reload favorites.txt back into the viewer
        try:
            if os.path.exists("src/tmp/favorites.txt"):
                with open("src/tmp/favorites.txt", "r") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    self.favorites_list = loaded
                    self.current_favorite_index = 0
                    
                    # Display all favorites at once
                    if callable(self.on_display_all_favorites):
                        self.on_display_all_favorites(self.favorites_list)
                    
                    # Highlight the first favorite if available
                    if self.favorites_list:
                        self._highlight_current_favorite()
                        self._update_favorites_header()
        except Exception as e:
            show_temporary_status(self.status_text, f"Failed to reload favorites: {e}", (1, 0, 0, 1), 3)
        
        if len(self.favorites_list) > 0:
            self.favorites_similar_button.show()

    def _remove_current_favorite(self):
        """Remove the currently selected favorite and refresh view/state.

        After removal, select the same index if it exists; otherwise select previous.
        """
        try:
            if not self.favorites_list:
                show_temporary_status(self.status_text, "No favorites to remove", (1, 1, 0, 1), 2)
                return

            idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))

            # Read current persisted favorites
            file_path = "src/tmp/favorites.txt"
            persisted = []
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        persisted = json.loads(content)

            if not persisted:
                show_temporary_status(self.status_text, "Favorites file empty", (1, 1, 0, 1), 2)
                return

            if idx >= len(persisted):
                idx = len(persisted) - 1

            # Remove entry at index
            del persisted[idx]

            # Save back
            with open(file_path, 'w') as f:
                json.dump(persisted, f, indent=2)

            # Update in-memory list
            self.favorites_list = persisted

            if not self.favorites_list:
                # Clear scene if none remain
                if hasattr(self, 'on_clear_favorite_objects') and callable(self.on_clear_favorite_objects):
                    self.on_clear_favorite_objects()
                self.current_favorite_index = 0
                self.favorites_header_text.setText("No favorites")
                show_temporary_status(self.status_text, "Removed. No favorites left.", (1, 1, 0, 1), 2)
                return

            # Choose new index per rule (we'll set it AFTER re-render to avoid resets)
            new_len = len(self.favorites_list)
            new_idx = idx if idx < new_len else idx - 1

            # Rebuild displayed favorites (this resets indices to 0 internally)
            if hasattr(self, 'on_clear_favorite_objects') and callable(self.on_clear_favorite_objects):
                self.on_clear_favorite_objects()
            if callable(self.on_display_all_favorites):
                self.on_display_all_favorites(self.favorites_list)

            # Now set intended selection and update view
            self.current_favorite_index = max(0, new_idx)
            # Focus camera and refresh header
            self._highlight_current_favorite()
            self._update_favorites_header()

            show_temporary_status(self.status_text, "Favorite removed", (0, 1, 0, 1), 2)
        except Exception as e:
            show_temporary_status(self.status_text, f"Remove failed: {e}", (1, 0, 0, 1), 3)

    def _render_current_favorite_info(self):
        if not self.favorites_list:
            self.favorites_info_text.setText("No favorites saved yet.")
            self.favorites_info_text.setFg((1, 1, 1, 1))
            self.favorites_info_text.show()
            return
        idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))
        entry = self.favorites_list[idx]
        object_type = entry.get("object_type", "Unknown")
        params = entry.get("parameters", {})
        header = f"Favorite {idx + 1}/{len(self.favorites_list)} — {object_type}"
        lines = [header]
        for key, val in params.items():
            lines.append(f"{key}: {val}")
        self.favorites_info_text.setText("\n".join(lines))
        self.favorites_info_text.setFg((1, 1, 1, 1))
        self.favorites_info_text.show()

    def _render_favorites_overview(self):
        """Render overview of all favorites."""
        if not self.favorites_list:
            self.favorites_info_text.setText("No favorites saved yet.")
            self.favorites_info_text.setFg((1, 1, 1, 1))
            self.favorites_info_text.show()
            return
        
        # Show current favorite details
        idx = self.current_favorite_index
        favorite = self.favorites_list[idx]
        object_type = favorite.get("object_type", "Unknown")
        timestamp = favorite.get("timestamp", "Unknown time")
        params = favorite.get("parameters", {})
        
        header = f"Favorite {idx + 1}/{len(self.favorites_list)} — {object_type}"
        timestamp_line = f"Created: {timestamp}"
        lines = [header, timestamp_line, ""]
        
        # Add parameter details
        for key, val in params.items():
            lines.append(f"{key}: {val:.2f}")
        
        self.favorites_info_text.setText("\n".join(lines))
        self.favorites_info_text.setFg((1, 1, 1, 1))
        self.favorites_info_text.show()

    def _toggle_dropdown(self):
        """Toggle dropdown open/closed state."""
        if self.dropdown_open:
            self.dropdown_frame.hide()
            self.dropdown_open = False
        else:
            self.dropdown_frame.show()
            self.dropdown_open = True

    def _select_option(self, option):
        """Select an option from the dropdown."""
        self.selected_option = option
        self.dropdown_button['text'] = option
        self.dropdown_frame.hide()
        self.dropdown_open = False
        print(f"Selected: {option}")
        # Notify listener about object change if provided
        if callable(self.on_object_change):
            self.on_object_change(option)

    def reset_to_defaults(self, object_type):
        """Reset sliders to default values and ranges for the given object type."""
        try:
            # Import here to avoid circular import issues at module load time
            from geometry.vase.config import vaseSliderConfig, vaseDefaults
            from geometry.table.config import tableSliderConfig, tableDefaults
            from geometry.stool.config import stoolSliderConfig, stoolDefaults

            if object_type == 'Table':
                param_configs = tableSliderConfig()
                defaults = tableDefaults()
            elif object_type == 'Stool':
                param_configs = stoolSliderConfig()
                defaults = stoolDefaults()
            else:
                param_configs = vaseSliderConfig()
                defaults = vaseDefaults()

            # Apply ranges and reset values/labels
            for (name, range_vals, default_val) in param_configs:
                if name in self.sliders:
                    self.sliders[name]['range'] = range_vals
                    new_value = defaults.get(name, default_val)
                    self.sliders[name]['value'] = new_value
                    if name in self.text_displays:
                        self.text_displays[name].setText(
                            format_slider_label_text(name, new_value)
                        )
                # If a slider does not exist (mismatched config), skip for now
        except Exception as e:
            # Keep UI resilient; log for debugging
            print(f"Failed to reset defaults for {object_type}: {e}")

    def get_all_parameters(self):
        """Get all current parameter values as a dictionary."""
        return get_all_parameters_from_sliders(self.sliders)

    def get_parameter(self, name):
        """Get a specific parameter value."""
        return self.sliders[name]["value"] if name in self.sliders else 0.0

    def set_favorites_list(self, favorites_list):
        """Set the favorites list for navigation."""
        self.favorites_list = favorites_list
        self.current_favorite_index = 0

    def show_overhang_warning(self):
        """Show the persistent overhang warning message."""
        self.overhang_warning_text.setText("Pull back on parameters, overhang is occurring")
        self.overhang_warning_text.show()

    def hide_overhang_warning(self):
        """Hide the overhang warning message."""
        self.overhang_warning_text.hide()
        self.overhang_warning_text.setText("")


# Keep the old class for backward compatibility
class HeightSlider(ParametricControls):
    """Legacy height slider for backward compatibility."""
    
    def __init__(self, on_height_change_callback):
        # Create a wrapper callback that extracts just the height
        def height_wrapper(params):
            on_height_change_callback(params.get("Height", 1.0))
        
        super().__init__(height_wrapper)
