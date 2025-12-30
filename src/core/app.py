#Panda3D base app class that handles windows, scenes, and rendering
from direct.showbase.ShowBase import ShowBase

# Panda3D node that contains the geometry
from panda3d.core import GeomNode

# Importing geometry from the new organized structure
from geometry.vase.geometry import vaseGeometry
from geometry.table.geometry import tableGeometry
from ExploreTab.Camera.exploreVaseCamera import vaseExploreCameraRound1Config
from geometry.vase.config import vaseSliderConfig, vaseDefaults
from geometry.table.config import tableSliderConfig, tableDefaults
from rendering.lighting import setup_lights

# Script that builds sliders and handles cha   nges
from ui.controls import ParametricControls

# Camera controller that handles the camera's movement and rotation
from camera.controller import OrbitCamera

## ShowBase is a class that provides the basic functionality for a Panda3D application.
class MainApp(ShowBase):
    """Main application class that coordinates all modules."""

    def __init__(self):
        # Initializes the Panda3D engine
        super().__init__()

        # Set white background
        self.win.setClearColor((1.0, 1.0, 1.0, 1))

        # Disables the default mouse control, so we can use our own camera controller
        self.disableMouse()  # use our own camera controller

        # Initialize with default parameters for Vase
        self.current_params = vaseDefaults()
        self.current_object_type = 'Vase'  # Set initial object type

        # Build initial cylinder
        self._rebuild_cylinder()

        # Setup the camera
        self._setup_camera_orbit()
        
        # Apply initial vase camera configuration
        from geometry.vase.config import vaseCameraConfig
        from panda3d.core import Vec3
        self.camera_controller.set_target(Vec3(0, 0, 0))  # Builder tab always targets origin
        self.camera_controller.apply_config(vaseCameraConfig())

        # Setup the lights
        setup_lights(self.render)

        # Setup the UI
        self._setup_ui()

    ## Functions that need to be called for the initial setup

    # Rebuild the cylinder with current parameters
    def _rebuild_cylinder(self):
        """Rebuild the cylinder with current parameters."""
        # Remove existing cylinder if it exists
        if hasattr(self, 'cylinder_np'):
            self.cylinder_np.removeNode()

        # Build new geometry with current parameters based on selected object type
        selected_type = getattr(self, 'current_object_type', 'Vace')
        if selected_type == 'Table':
            result = tableGeometry(
                segment_count=int(self.current_params["Segment Count"]),
                object_width=self.current_params["Object Width"],
                twist_angle=self.current_params["Twist Angle"],
                twist_groove_depth=self.current_params["Twist Groove Depth"],
                vertical_wave_freq=self.current_params["Vertical Wave Frequency"],
                vertical_wave_depth=self.current_params["Vertical Wave Depth"]
            )
        else:
            result = vaseGeometry(
                segment_count=int(self.current_params["Segment Count"]),
                object_width=self.current_params["Object Width"],
                twist_angle=self.current_params["Twist Angle"],
                twist_groove_depth=self.current_params["Twist Groove Depth"],
                vertical_wave_freq=self.current_params["Vertical Wave Frequency"],
                vertical_wave_depth=self.current_params["Vertical Wave Depth"]
            )
        if isinstance(result, tuple) and len(result) == 4:
            object_type, geom, material, has_overhang = result
        elif isinstance(result, tuple) and len(result) == 3:
            object_type, geom, material = result
            has_overhang = False
        elif isinstance(result, tuple) and len(result) == 2:
            object_type, geom = result
            material = None
            has_overhang = False
        else:
            object_type, geom = "Vase", result
            material = None

        # Create a new geometry node
        node = GeomNode("cylinder_node")
        node.addGeom(geom)
        
        # Apply material if provided
        if material:
            from panda3d.core import MaterialAttrib
            node.set_attrib(MaterialAttrib.make(material))
        
        # Attach the node to the render
        self.cylinder_np = self.render.attachNewNode(node)

        # Set the scale of the cylinder
        self.cylinder_np.setScale(1.0)

        # Store current object type for favorites saving
        self.current_object_type = object_type
        
        # Display overhang status (only print when overhang occurs)
        if has_overhang:
            print("WARNING: Overhang detected! Some areas exceed the maximum overhang angle.")
            # Show persistent overhang warning in UI
            if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'show_overhang_warning'):
                self.parametric_controls.show_overhang_warning()
        else:
            # Hide overhang warning in UI without printing
            if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'hide_overhang_warning'):
                self.parametric_controls.hide_overhang_warning()

        # (Removed) Do not update metrics here; update only on slider release

    def _setup_camera_orbit(self):
        """Setup the orbit camera controller."""
        self.camera_controller = OrbitCamera(self, self.cam, self.mouseWatcherNode)
        self.camera_controller.setup_task(self.taskMgr)

    def _setup_ui(self):
        """Setup the user interface."""
        # Provide a callable so UI can fetch the latest object type when saving favorites
        self.parametric_controls = ParametricControls(
            self._on_parameters_change,
            vaseSliderConfig,
            on_object_change_callback=self._on_object_change,
            get_current_object_type_callable=lambda: getattr(self, 'current_object_type', None),
            on_hide_object_callback=self._hide_object,
            on_show_object_callback=self._show_object,
            on_rebuild_with_params_callback=self._rebuild_with_params,
            on_display_all_favorites_callback=self._display_all_favorites,
            on_clear_favorite_objects_callback=self._clear_favorite_objects,
            on_highlight_favorite_callback=self._highlight_favorite,
            on_slider_released_callback=self._on_slider_released,
            on_display_round1_designs_callback=self._display_round1_designs
        )

        # Compute initial metrics so label is populated at startup
        try:
            self._on_slider_released()
        except Exception as e:
            print(f"Initial metrics update failed: {e}")

    def _on_slider_released(self):
        """Compute metrics from current geometry and update bottom label."""
        try:
            # Retrieve current displayed geometry
            if not hasattr(self, 'cylinder_np') or self.cylinder_np is None:
                return
            node = self.cylinder_np.node()
            if node is None or node.getNumGeoms() == 0:
                return
            geom = node.getGeom(0)

            # Compute metrics
            from MetricsCalc.metricData import compute_bb_from_geom, compute_volume_from_geom, LCA_data
            diameter, height = compute_bb_from_geom(geom)
            volume = compute_volume_from_geom(geom)
            mass, waterMetric, toyotaMetric, fordMetric, trashMetric = LCA_data(volume)

            # Format inches with 2 decimals for size, 2 decimals for trash metric
            label_text = f"Height: {height:.2f} in | Diameter: {diameter:.2f} in"
            # Visible label shows only the trash metric; details are in hover tooltip
            trash_text = f"Gallons of Recyled Trash Saved: {trashMetric:.2f} gallons"

            # Update UI labels
            if hasattr(self, 'parametric_controls'):
                if hasattr(self.parametric_controls, 'update_builder_label_text'):
                    self.parametric_controls.update_builder_label_text(label_text)
                if hasattr(self.parametric_controls, 'update_trash_metric_text'):
                    self.parametric_controls.update_trash_metric_text(trash_text)
                # Update hover tooltip with detailed metrics
                try:
                    tooltip = getattr(self.parametric_controls, 'trash_info_tooltip', None)
                    if tooltip is not None:
                        tooltip_text = (
                            f"Water Bottles Saved: {waterMetric:.2f}\n"
                            f"Miles Driven in 2020 Toyota Corolla: {toyotaMetric:.2f} miles\n"
                            f"Miles Driven in 2020 Ford F-150 AWD: {fordMetric:.2f} miles"
                        )
                        tooltip.setText(tooltip_text)
                except Exception:
                    pass
        except Exception as e:
            # Keep silent in UI, but print for debugging
            print(f"Metrics update failed: {e}")

    def _on_parameters_change(self, params):
        """Callback when any parameter changes."""
        self.current_params.update(params)
        self._rebuild_cylinder()

    def _on_object_change(self, selected_object_type: str):
        """Callback when the object type changes via the dropdown."""
        print(f"Object change called with: '{selected_object_type}'")
        self.current_object_type = selected_object_type
        # Reset UI sliders to object defaults and sync params
        if selected_object_type == 'Table':
            from geometry.table.config import tableDefaults, tableCameraConfig
            defaults = tableDefaults()
            camera_config = tableCameraConfig()
            print("Applied Table camera config")
        elif selected_object_type == 'Stool':
            from geometry.stool.config import stoolDefaults, stoolCameraConfig
            defaults = stoolDefaults()
            camera_config = stoolCameraConfig()
            print("Applied Stool camera config")
        else:
            from geometry.vase.config import vaseDefaults, vaseCameraConfig
            defaults = vaseDefaults()
            camera_config = vaseCameraConfig()
            print("Applied Vase camera config")

        # Update the app's current params and UI controls
        self.current_params.update(defaults)
        if hasattr(self, 'parametric_controls'):
            self.parametric_controls.reset_to_defaults(selected_object_type)
        
        # Apply object-specific camera configuration
        print(f"Applying camera config: {camera_config}")
        from panda3d.core import Vec3
        self.camera_controller.set_target(Vec3(0, 0, 0))  # Builder tab always targets origin
        self.camera_controller.apply_config(camera_config)

        # Rebuild with fresh defaults
        self._rebuild_cylinder()

    def _hide_object(self):
        """Hide the current 3D object from the screen."""
        if hasattr(self, 'cylinder_np'):
            self.cylinder_np.hide()

    def _show_object(self):
        """Show the current 3D object on the screen."""
        if hasattr(self, 'cylinder_np'):
            self.cylinder_np.show()

    def _rebuild_with_params(self, params, object_type=None):
        """Rebuild the object with new parameters and optionally change object type."""
        if object_type:
            self.current_object_type = object_type
        self.current_params.update(params)
        self._rebuild_cylinder()

    def _create_object_with_params(self, params, object_type="Vace", position=(0, 0, 0), scale=1.0):
        """Create a single object with given parameters at specified position."""
        # Build geometry with parameters based on object type
        if object_type == 'Table':
            from geometry.table.geometry import tableGeometry
            result = tableGeometry(
                segment_count=int(params["Segment Count"]),
                object_width=params["Object Width"],
                twist_angle=params["Twist Angle"],
                twist_groove_depth=params["Twist Groove Depth"],
                vertical_wave_freq=params["Vertical Wave Frequency"],
                vertical_wave_depth=params["Vertical Wave Depth"]
            )
        else:
            from geometry.vase.geometry import vaseGeometry
            result = vaseGeometry(
                segment_count=int(params["Segment Count"]),
                object_width=params["Object Width"],
                twist_angle=params["Twist Angle"],
                twist_groove_depth=params["Twist Groove Depth"],
                vertical_wave_freq=params["Vertical Wave Frequency"],
                vertical_wave_depth=params["Vertical Wave Depth"]
            )
        
        if isinstance(result, tuple) and len(result) == 4:
            actual_object_type, geom, material, has_overhang = result
        elif isinstance(result, tuple) and len(result) == 3:
            actual_object_type, geom, material = result
            has_overhang = False
        elif isinstance(result, tuple) and len(result) == 2:
            actual_object_type, geom = result
            material = None
            has_overhang = False
        else:
            actual_object_type, geom = object_type, result
            material = None
            has_overhang = False

        # Handle overhang warning display for this rebuild
        if has_overhang:
            if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'show_overhang_warning'):
                self.parametric_controls.show_overhang_warning()
        else:
            if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'hide_overhang_warning'):
                self.parametric_controls.hide_overhang_warning()

        # Create a new geometry node
        node = GeomNode(f"favorite_object_{actual_object_type}")
        node.addGeom(geom)
        
        # Apply material if provided
        if material:
            from panda3d.core import MaterialAttrib
            node.set_attrib(MaterialAttrib.make(material))

        # Attach the node to the render at specified position
        object_np = self.render.attachNewNode(node)
        object_np.setPos(position)
        object_np.setScale(scale)
        
        return object_np

    def _create_object_from_design(self, design):
        """Create a 3D object from design data."""
        try:
            params = design.get("parameters", {})
            object_type = design.get("object_type", "Vase")
            
            # Create the object using existing method
            obj = self._create_object_with_params(params, object_type, position=(0, 0, 0), scale=1.0)
            return obj
            
        except Exception as e:
            print(f"Error creating object from design: {e}")
            return None

    def _display_all_favorites(self, favorites_list):
        """Display all favorites objects in a grid with camera focusing on one at a time."""
        # Clear existing favorite objects
        if hasattr(self, 'favorite_objects'):
            for obj_np in self.favorite_objects:
                obj_np.removeNode()
        self.favorite_objects = []
        
        if not favorites_list:
            return
        
        # Store favorites list for navigation
        self.favorites_list = favorites_list
        self.current_favorite_index = 0
        
        # Display all favorites in a grid
        self._display_all_favorites_grid()
        
        # Set up camera to focus on the first favorite
        self._focus_camera_on_current_favorite()
        
        # Update UI with favorites list
        if hasattr(self, 'parametric_controls'):
            self.parametric_controls.set_favorites_list(favorites_list)

    def _display_round1_designs(self, designs_list):
        """Display Round 1 designs (8) in a static 4x2 grid without rotation."""
        # Clear any existing favorites objects
        if hasattr(self, 'favorite_objects'):
            for obj_np in self.favorite_objects:
                obj_np.removeNode()
        self.favorite_objects = []

        # Store and show in a grid
        self.favorites_list = designs_list or []
        if not self.favorites_list:
            return

        # Build 4x2 grid without rotation
        cols = 4
        spacing_x = 8.0
        spacing_z = 8.0
        # Center the grid
        start_x = -((cols - 1) * spacing_x) / 2
        start_z = spacing_z / 2  # top row positive z, bottom row negative z

        for i, favorite in enumerate(self.favorites_list):
            row = i // cols  # 0 or 1
            col = i % cols
            x = start_x + col * spacing_x
            z = start_z - row * spacing_z
            params = favorite.get("parameters", {})
            object_type = favorite.get("object_type", "Vase")
            obj_np = self._create_object_with_params(params, object_type, position=(x, 0, z), scale=1.0)
            self.favorite_objects.append(obj_np)

        # Show round instruction label at top
        try:
            from direct.gui.OnscreenText import OnscreenText
            from panda3d.core import TextNode
            if not hasattr(self, 'explore_header_text') or self.explore_header_text is None:
                self.explore_header_text = OnscreenText(
                    text="",
                    pos=(0, 0.9),
                    scale=0.07,
                    fg=(0, 0, 0, 1),
                    align=TextNode.ACenter,
                    mayChange=True,
                )
            self.explore_header_text.setText("Please rank all of the designs...")
            self.explore_header_text.show()
        except Exception:
            pass

        # Show star ratings for first 3 objects in top row
        try:
            from ExploreTab.star_rating import StarRating
            
            if not hasattr(self, 'design_star_ratings'):
                self.design_star_ratings = []
            
            # Track which designs have been rated
            if not hasattr(self, 'rated_designs'):
                self.rated_designs = set()  # Set of design indices that have been rated
            
            # Create star ratings for first 3 objects in top row
            # Using your perfect position: (-1.3, 0, 0) for top left
            star_positions = [
                (-1.3, 0, 0),  # Top left - your perfect position
                (-0.43, 0, 0),  # Top center - same z-plane
                (0.43, 0, 0),    # Top right - same z-plane
                (1.3, 0, 0),    # Top right - same z-plane
                (-1.3, 0, -.92),  # Top left - your perfect position
                (-0.43, 0, -.92),  # Top center - same z-plane
                (0.43, 0, -.92),    # Top right - same z-plane
                (1.3, 0, -.92),    # Top right - same z-plane

            ]
            
            for i in range(8):
                star_rating = StarRating(
                    pos=star_positions[i],
                    scale=0.05,
                    spacing=0.09,
                    design_index=i,
                    on_rating_callback=self._on_design_rated
                )
                
                self.design_star_ratings.append(star_rating)
            
            # Show all star ratings
            for i, star_rating in enumerate(self.design_star_ratings):
                star_rating.show()
                
        except Exception as e:
            pass

        # Apply explore camera
        try:
            from ExploreTab.Camera.exploreVaseCamera import vaseExploreCameraRound1Config
            cfg = vaseExploreCameraRound1Config()
            if hasattr(self, 'camera_controller'):
                self.camera_controller.apply_config(cfg)
                # Disable all user inputs in Explore
                self.camera_controller.disable_controls()
        except Exception:
            pass

    def _display_all_favorites_grid(self):
        """Display all favorites objects in a horizontal line layout."""
        if not hasattr(self, 'favorites_list') or not self.favorites_list:
            return
        
        # Calculate horizontal line layout
        total_favorites = len(self.favorites_list)
        spacing = 8.0  # Space between objects
        
        # Center the line horizontally
        start_x = -(total_favorites - 1) * spacing / 2
        
        for i, favorite in enumerate(self.favorites_list):
            # Calculate horizontal position
            x = start_x + i * spacing
            z = 0  # All objects in a single line
            
            # Create object at this position
            params = favorite.get("parameters", {})
            object_type = favorite.get("object_type", "Vace")
            
            obj_np = self._create_object_with_params(
                params, 
                object_type, 
                position=(x, 0, z),
                scale=1.0  # Smaller scale for line view
            )
            self.favorite_objects.append(obj_np)

    def _focus_camera_on_current_favorite(self):
        """Focus the camera on the currently selected favorite object."""
        if not hasattr(self, 'favorites_list') or not self.favorites_list:
            return
        
        # Stop any existing rotation animation
        self._stop_rotation_animation()
        
        # Calculate horizontal line layout to find the position of current favorite
        from panda3d.core import Vec3
        total_favorites = len(self.favorites_list)
        spacing = 8.0
        
        # Calculate position of current favorite
        start_x = -(total_favorites - 1) * spacing / 2
        target_x = start_x + self.current_favorite_index * spacing
        target_z = 0  # All objects in a single line
        
        # Store original camera state for returning to builder mode
        if not hasattr(self, 'original_camera_pos'):
            self.original_camera_pos = self.cam.getPos()
            self.original_camera_hpr = self.cam.getHpr()
        
        # Set the camera controller's target to the current favorite object
        if hasattr(self, 'camera_controller'):
            self.camera_controller.set_target(Vec3(target_x, 0, target_z))
            
            # Apply object-specific camera config based on the current favorite's object type
            current_favorite = self.favorites_list[self.current_favorite_index]
            object_type = current_favorite.get("object_type", "Vase")
            
            if object_type == 'Table':
                from geometry.table.config import tableCameraConfig
                camera_config = tableCameraConfig()
            elif object_type == 'Stool':
                from geometry.stool.config import stoolCameraConfig
                camera_config = stoolCameraConfig()
            else:  # Default to Vase
                from geometry.vase.config import vaseCameraConfig
                camera_config = vaseCameraConfig()
            
            # Apply the camera configuration
            self.camera_controller.apply_config(camera_config)
        
        # Re-enable camera controls for favorites view (now orbiting around the target object)
        if hasattr(self, 'camera_controller'):
            self.camera_controller.enable_controls()
        
        # Start rotation animation for the current favorite object
        self._start_rotation_animation()

    def _restore_camera_view(self):
        """Restore the original camera view for builder mode."""
        if hasattr(self, 'original_camera_pos') and hasattr(self, 'original_camera_hpr'):
            self.cam.setPos(self.original_camera_pos)
            self.cam.setHpr(self.original_camera_hpr)
        
        # Reset camera target back to origin for builder mode
        if hasattr(self, 'camera_controller'):
            from panda3d.core import Vec3
            self.camera_controller.set_target(Vec3(0, 0, 0))
        
        # Re-enable camera controls for builder mode
        if hasattr(self, 'camera_controller'):
            self.camera_controller.enable_controls()

    def _clear_favorite_objects(self):
        """Clear all favorite objects from the scene and restore camera."""
        # Stop rotation animation before clearing objects
        self._stop_rotation_animation()
        
        if hasattr(self, 'favorite_objects'):
            for obj_np in self.favorite_objects:
                obj_np.removeNode()
            self.favorite_objects = []
        # Hide explore header if present
        if hasattr(self, 'explore_header_text') and self.explore_header_text is not None:
            try:
                self.explore_header_text.hide()
                self.explore_header_text.setText("")
            except Exception:
                pass
        
        # Hide RoundReassure confidence text if present
        if hasattr(self, 'roundreassure_confidence_text') and self.roundreassure_confidence_text is not None:
            try:
                self.roundreassure_confidence_text.hide()
                self.roundreassure_confidence_text.setText("")
            except Exception:
                pass
        
        # Hide explore star ratings if present
        if hasattr(self, 'design_star_ratings') and self.design_star_ratings is not None:
            try:
                for star_rating in self.design_star_ratings:
                    star_rating.hide()
                    star_rating.destroy()
                self.design_star_ratings = []
            except Exception:
                pass
        
        # Hide RoundReassure star ratings if present
        if hasattr(self, 'roundreassure_star_ratings') and self.roundreassure_star_ratings is not None:
            try:
                for star_rating in self.roundreassure_star_ratings:
                    star_rating.hide()
                    star_rating.destroy()
                self.roundreassure_star_ratings = []
            except Exception:
                pass
        
        # Hide RoundFill star ratings if present
        if hasattr(self, 'roundfill_star_ratings') and self.roundfill_star_ratings is not None:
            try:
                for star_rating in self.roundfill_star_ratings:
                    star_rating.hide()
                    star_rating.destroy()
                self.roundfill_star_ratings = []
            except Exception:
                pass
        
        
        # Stop RoundFinal rotation animation if running
        if hasattr(self, 'taskMgr'):
            try:
                self.taskMgr.remove("roundfinal-rotation-task")
            except Exception:
                pass
        
        # Hide Next button if present
        if hasattr(self, 'next_button') and self.next_button is not None:
            try:
                self.next_button.hide()
            except Exception:
                pass
        
        # Hide RoundReassure Next button if present
        if hasattr(self, 'roundreassure_next_button') and self.roundreassure_next_button is not None:
            try:
                self.roundreassure_next_button.hide()
            except Exception:
                pass
        
        # Hide RoundFill Next button if present
        if hasattr(self, 'roundfill_next_button') and self.roundfill_next_button is not None:
            try:
                self.roundfill_next_button.hide()
            except Exception:
                pass
        
        # Reset rated designs tracking
        if hasattr(self, 'rated_designs'):
            self.rated_designs = set()
        
        # Reset RoundReassure rated designs tracking
        if hasattr(self, 'rated_roundreassure_designs'):
            self.rated_roundreassure_designs = set()
        
        # Reset RoundFill rated designs tracking
        if hasattr(self, 'rated_roundfill_designs'):
            self.rated_roundfill_designs = set()
        
        # Restore original camera view
        self._restore_camera_view()
    
    def _on_design_rated(self, design_index, rating):
        """Callback when a design is rated. Updates the Round1Designs.txt file."""
        try:
            import json
            import os
            
            # Path to the designs file
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            
            # Read current designs
            with open(designs_path, 'r', encoding='utf-8') as f:
                designs = json.load(f)
            
            # Update the rating for the specific design
            if 0 <= design_index < len(designs):
                designs[design_index]["Rating"] = rating
                
                # Write back to file
                with open(designs_path, 'w', encoding='utf-8') as f:
                    json.dump(designs, f, indent=2)
                
                
                # Track that this design has been rated
                self.rated_designs.add(design_index)
                
                # Check if all designs are rated and show "Next" button
                self._check_all_rated()
                
            else:
                print(f"[ERROR] Invalid design index: {design_index}")
                
        except Exception as e:
            print(f"[ERROR] Failed to update rating: {e}")
    
    def _check_all_rated(self):
        """Check if all 8 designs have been rated and show 'Next' button if so."""
        if len(self.rated_designs) >= 8:
            self._show_next_button()
    
    def _show_next_button(self):
        """Show the 'Next' button in the top right corner."""
        try:
            from direct.gui.DirectButton import DirectButton
            from direct.gui import DirectGuiGlobals as DGG
            
            # Only create the button if it doesn't exist
            if not hasattr(self, 'next_button') or self.next_button is None:
                self.next_button = DirectButton(
                    text="Next",
                    pos=(1.2, 0, 0.8),  # Top right corner
                    scale=0.06,
                    frameColor=(0.2, 0.8, 0.2, 1),  # Green color
                    relief="flat",
                    command=self._on_next_clicked
                )
            
            self.next_button.show()
            
        except Exception as e:
            pass
    
    def _on_next_clicked(self):
        """Handle Next button click (disabled for Explore redesign)."""
        return
    
    def _display_roundreassure_designs(self):
        """Display RoundReassure designs (last 3 designs from Designs.txt)."""
        try:
            import json
            import os
            
            # Read all designs from Designs.txt
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            if not os.path.exists(designs_path):
                return
            
            with open(designs_path, 'r', encoding='utf-8') as f:
                all_designs = json.load(f)
            
            # Get the last 3 designs (the new Round Reassure designs)
            designs = all_designs[-3:] if len(all_designs) >= 3 else all_designs
            
            
            # Display confidence metrics
            self._show_roundreassure_confidence()
            
            # Clear existing objects
            if hasattr(self, 'favorite_objects'):
                for obj_np in self.favorite_objects:
                    obj_np.removeNode()
                self.favorite_objects = []
            
            # Display 3 designs in a horizontal row (optimized for RoundReassure)
            num_designs = len(designs)
            spacing_x = 10.0  # Wider spacing for better visibility
            start_x = -((num_designs - 1) * spacing_x) / 2  # Center the row
            z = 0  # All designs on the same z-plane
            
            for i, design in enumerate(designs):
                x = start_x + i * spacing_x
                
                params = design.get("parameters", {})
                object_type = design.get("object_type", "Vase")
                obj_np = self._create_object_with_params(params, object_type, position=(x, 0, z), scale=1.0)
                self.favorite_objects.append(obj_np)
            
            # Add Round Reassure header text with coverage percentage
            coverage = getattr(self, 'roundreassure_coverage', None)
            self._show_roundreassure_header(coverage)
            
            # Create star rating components for RoundReassure designs
            try:
                from ExploreTab.star_rating import StarRating
                
                if not hasattr(self, 'roundreassure_star_ratings'):
                    self.roundreassure_star_ratings = []
                
                # Create star ratings for the 3 RoundReassure designs (hardcoded 2D positions)
                roundreassure_star_positions = [
                    (-1.1, 0, -0.5),  # Left design stars
                    (0, 0, -0.5),     # Center design stars  
                    (1.1, 0, -0.5)    # Right design stars
                ]
                
                for i in range(num_designs):
                    star_rating = StarRating(
                        pos=roundreassure_star_positions[i],
                        scale=0.05,
                        spacing=0.09,
                        design_index=i,
                        on_rating_callback=self._on_roundreassure_rated
                    )
                    
                    self.roundreassure_star_ratings.append(star_rating)
                
                # Show all star ratings
                for i, star_rating in enumerate(self.roundreassure_star_ratings):
                    star_rating.show()
                    
            except Exception as e:
                pass
            
            # Apply explore camera and disable controls
            try:
                from ExploreTab.Camera.exploreVaseCamera import vaseExploreCameraRound1Config
                cfg = vaseExploreCameraRound1Config()
                if hasattr(self, 'camera_controller'):
                    self.camera_controller.apply_config(cfg)
                    self.camera_controller.disable_controls()
            except Exception:
                pass
            
            
        except Exception as e:
            print(f"[ERROR] Failed to display RoundReassure designs: {e}")
    
    def _show_roundreassure_header(self, coverage_percentage=None):
        """Show header text for Round Reassure phase with design space coverage."""
        try:
            from direct.gui.OnscreenText import OnscreenText
            from panda3d.core import TextNode
            
            # Hide any existing header
            if hasattr(self, 'roundreassure_header_text'):
                self.roundreassure_header_text.hide()
            
            # Create header text with coverage percentage
            if coverage_percentage is not None:
                header_text = f"Design Space Coverage {coverage_percentage:.1f}%"
            else:
                header_text = "Round 2: Exploration & Exploitation"
            
            self.roundreassure_header_text = OnscreenText(
                text=header_text,
                pos=(0, 0.8),
                scale=0.06,
                fg=(0.2, 0.4, 0.8, 1),  # Blue color
                align=TextNode.ACenter,
                mayChange=True,
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to show Round Reassure header: {e}")
    
    def _display_roundfill_designs(self):
        """Display RoundFill designs (last 6 designs from Designs.txt) in 3x2 grid layout."""
        try:
            import json
            import os
            
            # Read all designs from Designs.txt
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            if not os.path.exists(designs_path):
                return
            
            with open(designs_path, 'r', encoding='utf-8') as f:
                all_designs = json.load(f)
            
            # Get the last 6 designs (the new Round Fill designs)
            designs = all_designs[-6:] if len(all_designs) >= 6 else all_designs
            
            # Add Round Fill header text with coverage percentage
            coverage = getattr(self, 'roundfill_coverage', None)
            self._show_roundreassure_header(coverage)
            
            # Clear existing objects
            if hasattr(self, 'favorite_objects'):
                for obj_np in self.favorite_objects:
                    obj_np.removeNode()
                self.favorite_objects = []
            
            # RoundFill layout configuration
            num_designs = len(designs)
            grid_cols = 3
            grid_rows = 2
            object_spacing_x = 10.0  # Horizontal spacing between 3D objects
            object_spacing_z = 8.0  # Vertical spacing between 3D objects
            object_scale = 1.0      # Scale factor for 3D objects
            
            # Calculate centered grid positions for 3D objects
            total_width = (grid_cols - 1) * object_spacing_x
            total_height = (grid_rows - 1) * object_spacing_z
            start_x = -total_width / 2  # Center horizontally
            start_z = total_height / 2  # Center vertically
            
            for i, design in enumerate(designs):
                # Calculate precise grid position
                row = i // grid_cols
                col = i % grid_cols
                
                x = start_x + col * object_spacing_x
                z = start_z - row * object_spacing_z
                
                params = design.get("parameters", {})
                object_type = design.get("object_type", "Vase")
                obj_np = self._create_object_with_params(params, object_type, position=(x, 0, z), scale=object_scale)
                self.favorite_objects.append(obj_np)
            
            # Create star rating components for RoundFill designs
            try:
                from ExploreTab.star_rating import StarRating
                
                if not hasattr(self, 'roundfill_star_ratings'):
                    self.roundfill_star_ratings = []
                
                # Hardcoded star positions for 3x2 grid (6 designs)
                roundfill_star_positions = [
                    (-1.1, 0, 0.0),   # Top row, left
                    (0.0, 0, 0.0),    # Top row, center
                    (1.1, 0, 0.0),    # Top row, right
                    (-1.1, 0, -0.95),  # Bottom row, left
                    (0.0, 0, -0.95),   # Bottom row, center
                    (1.1, 0, -0.95),   # Bottom row, right
                ]
                
                star_scale = 0.05    # Scale factor for star ratings
                star_group_spacing = 0.09  # Spacing between individual stars
                
                for i in range(num_designs):
                    star_rating = StarRating(
                        pos=roundfill_star_positions[i],
                        scale=star_scale,
                        spacing=star_group_spacing,
                        design_index=i,
                        on_rating_callback=self._on_roundfill_rated
                    )
                    
                    self.roundfill_star_ratings.append(star_rating)
                
                # Show all star ratings
                for i, star_rating in enumerate(self.roundfill_star_ratings):
                    star_rating.show()
                    
            except Exception as e:
                pass
            
            # Apply explore camera and disable controls
            try:
                from ExploreTab.Camera.exploreVaseCamera import vaseExploreCameraRound1Config
                cfg = vaseExploreCameraRound1Config()
                if hasattr(self, 'camera_controller'):
                    self.camera_controller.apply_config(cfg)
                    self.camera_controller.disable_controls()
            except Exception:
                pass
            
        except Exception as e:
            print(f"[ERROR] Failed to display RoundFill designs: {e}")

    def _display_roundfinal_designs(self):
        """Display the RoundFinal designs (final recommendations)."""
        try:
            import json
            import os
            
            # Read the last designs from Designs.txt
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            
            if not os.path.exists(designs_path):
                print(f"Designs file not found: {designs_path}")
                return
            
            with open(designs_path, 'r', encoding='utf-8') as f:
                all_designs = json.load(f)
            
            # Get the last 6 designs (final recommendations)
            designs = all_designs[-6:] if len(all_designs) >= 6 else all_designs
            
            if not designs:
                print("No designs found for RoundFinal display")
                return
            
            # Clear existing objects
            self._clear_favorite_objects()
            
            # Display header
            self._show_roundfinal_header()
            
            # RoundFinal layout configuration (exact same as RoundFill)
            num_designs = len(designs)
            grid_cols = 3
            grid_rows = 2
            object_spacing_x = 10.0  # Horizontal spacing between 3D objects
            object_spacing_z = 8.0  # Vertical spacing between 3D objects
            object_scale = 1.0      # Scale factor for 3D objects
            
            # Calculate centered grid positions for 3D objects
            total_width = (grid_cols - 1) * object_spacing_x
            total_height = (grid_rows - 1) * object_spacing_z
            start_x = -total_width / 2  # Center horizontally
            start_z = total_height / 2  # Center vertically
            
            for i, design in enumerate(designs):
                # Calculate precise grid position
                row = i // grid_cols
                col = i % grid_cols
                
                x = start_x + col * object_spacing_x
                z = start_z - row * object_spacing_z
                
                params = design.get("parameters", {})
                object_type = design.get("object_type", "Vase")
                obj_np = self._create_object_with_params(params, object_type, position=(x, 0, z), scale=object_scale)
                self.favorite_objects.append(obj_np)
                
                print(f"Displayed RoundFinal design {i+1}: {design.get('parameters', {})}")
            
            # Start rotation animation for all RoundFinal objects
            self._start_roundfinal_rotation_animation()
            
            # Disable camera controls for final round viewing
            if hasattr(self, 'camera_controller'):
                self.camera_controller.disable_controls()
            
            print(f"Displayed {len(designs)} RoundFinal designs")
            
        except Exception as e:
            print(f"Error displaying RoundFinal designs: {e}")

    def _show_roundfinal_header(self):
        """Show the RoundFinal header with final recommendations message."""
        try:
            from direct.gui.OnscreenText import OnscreenText
            from panda3d.core import TextNode
            
            # Hide any existing confidence text
            if hasattr(self, 'roundfinal_confidence_text'):
                self.roundfinal_confidence_text.hide()
            
            # Show final recommendations header
            self.roundfinal_confidence_text = OnscreenText(
                text="🎯 FINAL RECOMMENDATIONS",
                pos=(0, 0.9),
                scale=0.06,
                fg=(0.2, 0.8, 0.2, 1),  # Green color
                align=TextNode.ACenter,
                mayChange=False,
            )
            self.roundfinal_confidence_text.show()
            
        except Exception as e:
            pass

    def _on_roundfill_rated(self, design_index, rating):
        """Callback when a RoundFill design is rated. Updates the Designs.txt file."""
        try:
            import json
            import os
            
            # Path to the Designs.txt file
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            
            # Read all designs
            with open(designs_path, 'r', encoding='utf-8') as f:
                all_designs = json.load(f)
            
            # Calculate the actual index in the full designs list
            # Round Fill designs are the last 6, so we need to map the display index to the actual index
            if len(all_designs) >= 6:
                # Get the last 6 designs and update the rating
                actual_index = len(all_designs) - 6 + design_index
                if 0 <= actual_index < len(all_designs):
                    all_designs[actual_index]["Rating"] = rating
                    
                    # Write back to file
                    with open(designs_path, 'w', encoding='utf-8') as f:
                        json.dump(all_designs, f, indent=2)
                
                # Track that this design has been rated
                if not hasattr(self, 'rated_roundfill_designs'):
                    self.rated_roundfill_designs = set()
                self.rated_roundfill_designs.add(design_index)
                
                # Check if all RoundFill designs are rated and show "Next" button
                self._check_all_roundfill_rated()
                
            else:
                print(f"[ERROR] Invalid RoundFill design index: {design_index}")
                
        except Exception as e:
            print(f"[ERROR] Failed to update RoundFill rating: {e}")

    def _check_all_roundfill_rated(self):
        """Check if all 6 RoundFill designs have been rated and show 'Next' button if so."""
        if hasattr(self, 'rated_roundfill_designs') and len(self.rated_roundfill_designs) >= 6:
            self._show_roundfill_next_button()

    def _show_roundfill_next_button(self):
        """Show the 'Next' button for RoundFill in the top right corner."""
        try:
            from direct.gui.DirectButton import DirectButton
            from direct.gui import DirectGuiGlobals as DGG
            
            # Only create the button if it doesn't exist
            if not hasattr(self, 'roundfill_next_button') or self.roundfill_next_button is None:
                self.roundfill_next_button = DirectButton(
                    text="Next",
                    pos=(1.2, 0, 0.8),  # Top right corner
                    scale=0.06,
                    frameColor=(0.2, 0.8, 0.2, 1),  # Green color
                    relief="flat",
                    command=self._on_roundfill_next_clicked
                )
            
            self.roundfill_next_button.show()
            
        except Exception as e:
            pass

    def _on_roundfill_next_clicked(self):
        """Handle RoundFill Next button click (disabled for Explore redesign)."""
        return
    
    def _on_roundreassure_rated(self, design_index, rating):
        """Callback when a RoundReassure design is rated. Updates the Designs.txt file."""
        try:
            import json
            import os
            
            # Path to the Designs.txt file
            designs_path = os.path.join("src", "ExploreTab", "Bayesian", "Designs.txt")
            
            # Read all designs
            with open(designs_path, 'r', encoding='utf-8') as f:
                all_designs = json.load(f)
            
            # Calculate the actual index in the full designs list
            # Round Reassure designs are the last 3, so we need to map the display index to the actual index
            if len(all_designs) >= 3:
                # Get the last 3 designs and update the rating
                actual_index = len(all_designs) - 3 + design_index
                if 0 <= actual_index < len(all_designs):
                    all_designs[actual_index]["Rating"] = rating
                    
                    # Write back to file
                    with open(designs_path, 'w', encoding='utf-8') as f:
                        json.dump(all_designs, f, indent=2)
                
                
                # Track that this design has been rated
                if not hasattr(self, 'rated_roundreassure_designs'):
                    self.rated_roundreassure_designs = set()
                self.rated_roundreassure_designs.add(design_index)
                
                # Check if all RoundReassure designs are rated and show "Next" button
                self._check_all_roundreassure_rated()
                
            else:
                print(f"[ERROR] Invalid RoundReassure design index: {design_index}")
                
        except Exception as e:
            print(f"[ERROR] Failed to update RoundReassure rating: {e}")

    def _append_designs_to_alldesigns(self, source_file):
        """Append designs from source file to AllDesigns.txt for training."""
        try:
            import json
            import os
            
            # Paths
            tmp_explore_path = os.path.join("src", "ExploreTab", "Bayesian", "tmp_explore")
            source_path = os.path.join(tmp_explore_path, source_file)
            alldesigns_path = os.path.join(tmp_explore_path, "AllDesigns.txt")
            
            # Read source designs
            if not os.path.exists(source_path):
                return
                
            with open(source_path, 'r', encoding='utf-8') as f:
                source_designs = json.load(f)
            
            # Extract training data (parameters and rating)
            training_designs = []
            for design in source_designs:
                if design.get("Rating") is not None:  # Only include rated designs
                    training_design = {
                        "parameters": design.get("parameters", {}),
                        "Rating": design.get("Rating"),
                        "object_type": design.get("object_type")
                    }
                    training_designs.append(training_design)
            
            # Read existing AllDesigns or create new
            all_designs = []
            if os.path.exists(alldesigns_path):
                with open(alldesigns_path, 'r', encoding='utf-8') as f:
                    all_designs = json.load(f)
            
            # Append new designs
            all_designs.extend(training_designs)
            
            # Write back to AllDesigns.txt
            with open(alldesigns_path, 'w', encoding='utf-8') as f:
                json.dump(all_designs, f, indent=2)
            
            
        except Exception as e:
            print(f"[ERROR] Failed to append designs to AllDesigns.txt: {e}")

    def _check_all_roundreassure_rated(self):
        """Check if all 3 RoundReassure designs have been rated and show 'Next' button if so."""
        if hasattr(self, 'rated_roundreassure_designs') and len(self.rated_roundreassure_designs) >= 3:
            self._show_roundreassure_next_button()

    def _show_roundreassure_next_button(self):
        """Show the 'Next' button for RoundReassure in the top right corner."""
        try:
            from direct.gui.DirectButton import DirectButton
            from direct.gui import DirectGuiGlobals as DGG
            
            # Only create the button if it doesn't exist
            if not hasattr(self, 'roundreassure_next_button') or self.roundreassure_next_button is None:
                self.roundreassure_next_button = DirectButton(
                    text="Next",
                    pos=(1.2, 0, 0.8),  # Top right corner
                    scale=0.06,
                    frameColor=(0.2, 0.8, 0.2, 1),  # Green color
                    relief="flat",
                    command=self._on_roundreassure_next_clicked
                )
            
            self.roundreassure_next_button.show()
            
        except Exception as e:
            pass

    def _on_roundreassure_next_clicked(self):
        """Handle RoundReassure Next button click (disabled for Explore redesign)."""
        return

    def _show_roundreassure_confidence(self):
        """Display confidence metrics for RoundReassure phase."""
        try:
            from direct.gui.OnscreenText import OnscreenText
            from panda3d.core import TextNode
            
            # Only show if we have confidence data
            if not hasattr(self, 'roundreassure_confidence'):
                return
                
            confidence = self.roundreassure_confidence
            confidence_percent = confidence * 100
            
            # Create confidence text if it doesn't exist
            if not hasattr(self, 'roundreassure_confidence_text') or self.roundreassure_confidence_text is None:
                self.roundreassure_confidence_text = OnscreenText(
                    text="",
                    pos=(0, 0.8),
                    scale=0.06,
                    fg=(0.2, 0.4, 0.8, 1),  # Blue color
                    align=TextNode.ACenter,
                    mayChange=True,
                )
            
            # Set confidence text
            confidence_text = f"Model Confidence: {confidence_percent:.1f}%"
            self.roundreassure_confidence_text.setText(confidence_text)
            self.roundreassure_confidence_text.show()
            
        except Exception as e:
            pass

    def _run_round_final(self, designs_path, object_type):
        """Run RoundFinal when convergence threshold is reached."""
        try:
            from utils.ui_utils import show_temporary_status
            # Access status_text through parametric_controls
            if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'status_text'):
                show_temporary_status(self.parametric_controls.status_text, "Running final round...", (0.2, 0.8, 0.2, 1), 3)
            
            # Call the self-contained RoundFinal function
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ExploreTab', 'Bayesian'))
            from src.ExploreTab.Bayesian.RoundFinal import RoundFinal
            
            # Call RoundFinal
            roundfinal_result = RoundFinal(designs_path, object_type)
            
            # Clear the screen of current objects
            self._clear_favorite_objects()
            
            # Display the RoundFinal results
            self._display_roundfinal_designs()
            
            print(f"🎯 RoundFinal completed successfully")
            
        except Exception as e:
            print(f"Error running RoundFinal: {e}")
            try:
                if hasattr(self, 'parametric_controls') and hasattr(self.parametric_controls, 'status_text'):
                    show_temporary_status(self.parametric_controls.status_text, f"Error: {e}", (0.8, 0.2, 0.2, 1), 3)
            except Exception:
                pass

    def _start_rotation_animation(self):
        """Start slow rotation animation for the currently selected favorite object."""
        if not hasattr(self, 'favorite_objects') or not self.favorite_objects:
            return
        
        if self.current_favorite_index >= len(self.favorite_objects):
            return
        
        # Get the current favorite object
        self.rotating_object = self.favorite_objects[self.current_favorite_index]
        
        # Start rotation task
        self.taskMgr.add(self._rotation_task, "favorite-rotation-task")

    def _stop_rotation_animation(self):
        """Stop the rotation animation."""
        self.taskMgr.remove("favorite-rotation-task")
        self.rotating_object = None

    def _rotation_task(self, task):
        """Task that rotates the selected favorite object slowly."""
        if hasattr(self, 'rotating_object') and self.rotating_object:
            # Rotate 1 degree per frame (adjust speed as needed)
            self.rotating_object.setH(self.rotating_object.getH() + 1)
        return task.cont

    def _start_roundfinal_rotation_animation(self):
        """Start rotation animation for all RoundFinal objects."""
        if not hasattr(self, 'favorite_objects') or not self.favorite_objects:
            return
        
        # Start rotation task for RoundFinal objects
        self.taskMgr.add(self._roundfinal_rotation_task, "roundfinal-rotation-task")

    def _stop_roundfinal_rotation_animation(self):
        """Stop the RoundFinal rotation animation."""
        self.taskMgr.remove("roundfinal-rotation-task")

    def _roundfinal_rotation_task(self, task):
        """Task that rotates all RoundFinal objects slowly."""
        if hasattr(self, 'favorite_objects') and self.favorite_objects:
            # Rotate all objects 0.5 degrees per frame (very slow)
            for obj in self.favorite_objects:
                if obj:
                    obj.setH(obj.getH() + 0.5)
        return task.cont

    def _highlight_favorite(self, favorite_index):
        """Focus camera on a different favorite object."""
        if not hasattr(self, 'favorites_list') or not self.favorites_list:
            return
        
        # Update current index
        self.current_favorite_index = favorite_index
        
        # Focus camera on the selected favorite
        self._focus_camera_on_current_favorite()

    # ===== Tournament (Vase) - minimal, single-camera, locked orbit =====
    def start_batch1_tournament(self):
        """Load Batch1 tournament data and display the current head-to-head match."""
        try:
            import os, json, random
            # Load designs
            designs_path = os.path.join("src", "ExploreTab", "tmp", "designs.txt")
            with open(designs_path, "r", encoding="utf-8") as f:
                self.tournament_designs = json.load(f)
            # Build initial matches in-memory (no file)
            # Read config for shuffle/seed
            try:
                conf_path = os.path.join("src", "ExploreTab", "Configuration.JSON")
                with open(conf_path, "r", encoding="utf-8") as cf:
                    conf = json.load(cf)
                tconf = conf.get("Batch 1 Tournament", {})
                shuffle = bool(tconf.get("shuffle", True))
                seed = tconf.get("seed", None)
            except Exception:
                shuffle, seed = True, None
            idx = list(range(len(self.tournament_designs)))
            rnd = random.Random(seed)
            if shuffle:
                rnd.shuffle(idx)
            # Handle bye (odd count): carry last forward
            self.tournament_next_indices = []
            if len(idx) % 2 == 1:
                self.tournament_next_indices.append(idx.pop())
            # Pair remaining indices
            matches = []
            for i in range(0, len(idx), 2):
                a = idx[i]
                b = idx[i + 1]
                matches.append({
                    "match_id": len(matches) + 1,
                    "a_index": a,
                    "b_index": b
                })
            self.tournament_matches = matches
            # Init round and index
            self.tournament_round = 1
            self.tournament_idx = 0
            # Apply vase explore camera config and lock controls
            try:
                from ExploreTab.Camera.exploreVaseCamera import vaseExploreCameraRound1Config
                cfg = vaseExploreCameraRound1Config()
                self.camera_controller.apply_config(cfg)
                from panda3d.core import Vec3
                self.camera_controller.set_target(Vec3(0, 0, 0))
                self.camera_controller.disable_controls()
            except Exception:
                pass
            # Show first match
            self._show_batch1_tournament_match()
        except Exception as e:
            print(f"[Tournament] Failed to start: {e}")

    def _clear_tournament_ui(self):
        """Remove tournament objects, labels, and buttons from the scene."""
        try:
            # Stop rotation task
            try:
                self.taskMgr.remove("tournament-rotation-task")
            except Exception:
                pass
            # Remove objects
            if hasattr(self, 'tournament_objects'):
                for obj_np in self.tournament_objects:
                    try:
                        obj_np.removeNode()
                    except Exception:
                        pass
            self.tournament_objects = []
            # Hide labels
            if hasattr(self, 'tournament_labels'):
                for label in self.tournament_labels:
                    try:
                        label.hide()
                        label.destroy()
                    except Exception:
                        pass
            self.tournament_labels = []
            # Hide title
            if hasattr(self, 'tournament_title') and self.tournament_title is not None:
                try:
                    self.tournament_title.hide()
                    self.tournament_title.destroy()
                except Exception:
                    pass
                self.tournament_title = None
            # Hide buttons
            if hasattr(self, 'tournament_buttons'):
                for btn in self.tournament_buttons:
                    try:
                        btn.hide()
                        btn.destroy()
                    except Exception:
                        pass
            self.tournament_buttons = []
        except Exception:
            pass

    def _show_batch1_tournament_match(self):
        """Render current match (two vases) with name labels and pick buttons."""
        try:
            # Bounds check
            if not hasattr(self, 'tournament_matches') or self.tournament_idx >= len(self.tournament_matches):
                print("[Tournament] No more matches.")
                self._clear_tournament_ui()
                return
            match = self.tournament_matches[self.tournament_idx]
            a_idx, b_idx = match["a_index"], match["b_index"]
            a = self.tournament_designs[a_idx]
            b = self.tournament_designs[b_idx]

            # Clear any previous UI
            self._clear_tournament_ui()

            # Render two objects
            self.tournament_objects = []
            from ExploreTab.Camera.exploreVaseCamera import vaseTournamentLayout
            layout = vaseTournamentLayout()
            # Store spin speed for rotation task
            self.tournament_spin_speed = layout.get("spin_speed", 0.8)
            a_np = self._create_object_with_params(
                a["parameters"], a.get("object_type", "Vase"),
                position=layout["left"], scale=layout.get("scale", 1.0)
            )
            b_np = self._create_object_with_params(
                b["parameters"], b.get("object_type", "Vase"),
                position=layout["right"], scale=layout.get("scale", 1.0)
            )
            self.tournament_objects.extend([a_np, b_np])

            # Start rotation
            self._start_tournament_rotation()

            # No labels for the tournament objects (titles removed)
            self.tournament_labels = []

            # Title above the models
            try:
                from direct.gui.OnscreenText import OnscreenText
                from panda3d.core import TextNode
                self.tournament_title = OnscreenText(
                    text="Choose your preferred design",
                    pos=(0, 0.92),
                    scale=0.08,
                    fg=(0, 0, 0, 1),
                    align=TextNode.ACenter,
                    mayChange=False,
                )
                self.tournament_title.show()
            except Exception:
                self.tournament_title = None

            # Overlay click zones (debug-colored) over each model
            from direct.gui.DirectButton import DirectButton
            self.tournament_buttons = [
                DirectButton(
                    text="",
                    pos=(-0.6, 0, 0.0),   # roughly over left model
                    relief="flat",
                    frameColor=(1, 1., 1, 0),  # semi-transparent green for debugging
                    frameSize=(-.75, 0.6, -0.6, 0.75), # make the box large to cover the model
                    command=lambda: self._on_tournament_pick(match, a_idx),
                ),
                DirectButton(
                    text="",
                    pos=(0.6, 0, 0.0),    # roughly over right model
                    relief="flat",
                    frameColor=(1, 1, 1, 0),  # semi-transparent blue for debugging
                    frameSize=(-0.6, 0.75, -0.6, 0.75),
                    command=lambda: self._on_tournament_pick(match, b_idx),
                ),
            ]
            for btn in self.tournament_buttons:
                btn.show()

            # Hover tint: turn the corresponding object green while hovering the button
            try:
                from direct.gui import DirectGuiGlobals as DGG
                # Button A hover
                self.tournament_buttons[0].bind(DGG.ENTER, lambda _evt: self._tint_object(self.tournament_objects[0], True))
                self.tournament_buttons[0].bind(DGG.EXIT, lambda _evt: self._tint_object(self.tournament_objects[0], False))
                # Button B hover
                self.tournament_buttons[1].bind(DGG.ENTER, lambda _evt: self._tint_object(self.tournament_objects[1], True))
                self.tournament_buttons[1].bind(DGG.EXIT, lambda _evt: self._tint_object(self.tournament_objects[1], False))
            except Exception:
                pass
        except Exception as e:
            print(f"[Tournament] Display error: {e}")

    def _on_tournament_pick(self, match, winner_index):
        """Record pick to results file and advance to next match."""
        try:
            import os, json
            a_index, b_index = match["a_index"], match["b_index"]
            winner_name = self.tournament_designs[winner_index].get("Name", "")
            record = {
                "match_id": match["match_id"],
                "a_index": a_index,
                "b_index": b_index,
                "winner_index": winner_index,
                "winner_name": winner_name,
                "round": getattr(self, "tournament_round", 1)
            }
            out_path = os.path.join("src", "ExploreTab", "tmp", "Batch1TournamentResults.txt")
            results = []
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        results = json.load(f)
                except Exception:
                    results = []
            results.append(record)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            # Accumulate winner for next round
            if not hasattr(self, "tournament_next_indices") or self.tournament_next_indices is None:
                self.tournament_next_indices = []
            self.tournament_next_indices.append(winner_index)
            # Advance to next match in current round or build next round
            self.tournament_idx += 1
            if self.tournament_idx >= len(self.tournament_matches):
                # End of current round
                winners = list(self.tournament_next_indices)
                # If only one winner remains, tournament is finished
                if len(winners) <= 1:
                    # Generate final tournament plot (after all rounds complete)
                    try:
                        from ExploreTab.Extra.TournamentPlot import plot_tournament
                        designs_path = os.path.join("src", "ExploreTab", "tmp", "designs.txt")
                        results_path = os.path.join("src", "ExploreTab", "tmp", "Batch1TournamentResults.txt")
                        # Also write simplified pairwise comparisons
                        try:
                            with open(results_path, "r", encoding="utf-8") as rf:
                                _matches = json.load(rf)
                            comparisons_list = []
                            for m in _matches:
                                a_i = m.get("a_index")
                                b_i = m.get("b_index")
                                w_i = m.get("winner_index")
                                if w_i is None or a_i is None or b_i is None:
                                    continue
                                loser = b_i if w_i == a_i else a_i
                                comparisons_list.append((int(w_i), int(loser)))
                            ratings_path = os.path.join("src", "ExploreTab", "tmp", "designsRatings.txt")
                            with open(ratings_path, "w", encoding="utf-8") as wf:
                                wf.write("comparisons = [\n")
                                for w_i, l_i in comparisons_list:
                                    wf.write(f"    ({w_i},{l_i}),\n")
                                wf.write("]\n")
                        except Exception:
                            pass
                        images_dir = os.path.join("src", "ExploreTab", "Images")
                        try:
                            os.makedirs(images_dir, exist_ok=True)
                        except Exception:
                            pass
                        output_png = os.path.join(images_dir, "TournamentResults.png")
                        plot_tournament(designs_path, results_path, output_path=output_png)
                        # Update designs.txt with latent ratings computed from pairwise results
                        try:
                            from ExploreTab.Extra.LatentMetric import update_designs_ratings
                            update_designs_ratings(designs_path, ratings_path)
                            # Train Bayesian model on updated designs
                            try:
                                from ExploreTab.BayesTrain import run_bayes_train
                                print("[Explore] Training Bayesian model...")
                                run_bayes_train(designs_path)
                                print("[Explore] Training complete.")
                            except Exception as e:
                                print(f"[Explore] Training failed: {e}")
                        except Exception:
                            pass
                    except Exception:
                        pass

                    # Show post-tournament instruction overlay (3s window with fade in/out)
                    try:
                        from direct.showbase.ShowBaseGlobal import base
                        from direct.gui.DirectFrame import DirectFrame
                        from direct.gui.OnscreenText import OnscreenText
                        from panda3d.core import TextNode

                        # Ensure prior tournament UI is cleared so screen is blank
                        self._clear_tournament_ui()

                        # Fullscreen transparent overlay (blocks clicks)
                        self._post_overlay = DirectFrame(
                            pos=(0, 0, 0),
                            frameColor=(1, 1, 1, 0),
                            frameSize=(-1.6, 1.6, -0.95, 0.95),
                            relief="flat",
                        )
                        # Small white panel behind text
                        self._post_panel = DirectFrame(
                            pos=(0, 0, 0),
                            frameColor=(1, 1, 1, 1),
                            frameSize=(-0.9, 0.9, -0.35, 0.35),
                            relief="flat",
                        )
                        self._post_panel.reparentTo(self._post_overlay)
                        # Instruction text (start transparent for fade-in)
                        self._post_text = OnscreenText(
                            text="Creating more models you may like....",
                            pos=(0, 0.0),
                            scale=0.07,
                            fg=(0, 0, 0, 0),
                            align=TextNode.ACenter,
                            mayChange=True,
                        )
                        self._post_text.reparentTo(self._post_panel)

                        # Fade-in (longer: 1.2s), with a brief blank pre-delay before starting
                        def _post_fade_in(task):
                            try:
                                duration = 1.2
                                t = min(1.0, task.time / duration)
                                if hasattr(self, "_post_text") and self._post_text is not None:
                                    self._post_text.setFg((0, 0, 0, t))
                                return task.done if t >= 1.0 else task.cont
                            except Exception:
                                return task.done

                        # Start fade-out sequence
                        def _post_start_fade_out(task):
                            def _post_fade_out(tk):
                                try:
                                    duration = 0.6
                                    t = min(1.0, tk.time / duration)
                                    a = max(0.0, 1.0 - t)
                                    if hasattr(self, "_post_text") and self._post_text is not None:
                                        self._post_text.setFg((0, 0, 0, a))
                                    return tk.done if t >= 1.0 else tk.cont
                                except Exception:
                                    return tk.done
                            base.taskMgr.add(_post_fade_out, "post-tournament-fade-out")

                            # Cleanup overlay after fade-out completes, then show Round 2 overlay
                            def _post_cleanup(tsk):
                                try:
                                    if hasattr(self, "_post_text") and self._post_text is not None:
                                        self._post_text.hide()
                                        self._post_text.destroy()
                                        self._post_text = None
                                    if hasattr(self, "_post_panel") and self._post_panel is not None:
                                        self._post_panel.hide()
                                        self._post_panel.destroy()
                                        self._post_panel = None
                                    if hasattr(self, "_post_overlay") and self._post_overlay is not None:
                                        self._post_overlay.hide()
                                        self._post_overlay.destroy()
                                        self._post_overlay = None
                                except Exception:
                                    pass

                                # Begin Round 2 overlay sequence
                                try:
                                    # Fullscreen transparent overlay
                                    self._round2_overlay = DirectFrame(
                                        pos=(0, 0, 0),
                                        frameColor=(1, 1, 1, 0),
                                        frameSize=(-1.6, 1.6, -0.95, 0.95),
                                        relief="flat",
                                    )
                                    # Small white panel behind text
                                    self._round2_panel = DirectFrame(
                                        pos=(0, 0, 0),
                                        frameColor=(1, 1, 1, 1),
                                        frameSize=(-0.9, 0.9, -0.35, 0.35),
                                        relief="flat",
                                    )
                                    self._round2_panel.reparentTo(self._round2_overlay)
                                    # Text start transparent
                                    self._round2_text = OnscreenText(
                                        text="Round 2:\n\nPlease select your preferred designs. Use the sliders to customize them as needed...",
                                        pos=(0, 0.0),
                                        scale=0.07,
                                        fg=(0, 0, 0, 0),
                                        align=TextNode.ACenter,
                                        mayChange=True,
                                    )
                                    self._round2_text.reparentTo(self._round2_panel)

                                    # Fade in (1.2s)
                                    def _r2_fade_in(t_in):
                                        try:
                                            dur = 1.2
                                            tt = min(1.0, t_in.time / dur)
                                            if hasattr(self, "_round2_text") and self._round2_text is not None:
                                                self._round2_text.setFg((0, 0, 0, tt))
                                            return t_in.done if tt >= 1.0 else t_in.cont
                                        except Exception:
                                            return t_in.done

                                    base.taskMgr.add(_r2_fade_in, "round2-fade-in")

                                    # Start fade out after hold (2.7s hold after fade-in; total ~4.5s with 1.2s in + 0.6s out)
                                    def _r2_start_fade_out(tk0):
                                        def _r2_fade_out(tk1):
                                            try:
                                                dur = 0.6
                                                tt = min(1.0, tk1.time / dur)
                                                a = max(0.0, 1.0 - tt)
                                                if hasattr(self, "_round2_text") and self._round2_text is not None:
                                                    self._round2_text.setFg((0, 0, 0, a))
                                                return tk1.done if tt >= 1.0 else tk1.cont
                                            except Exception:
                                                return tk1.done
                                        base.taskMgr.add(_r2_fade_out, "round2-fade-out")

                                        # Cleanup round2 overlay
                                        def _r2_cleanup(tk2):
                                            try:
                                                if hasattr(self, "_round2_text") and self._round2_text is not None:
                                                    self._round2_text.hide()
                                                    self._round2_text.destroy()
                                                    self._round2_text = None
                                                if hasattr(self, "_round2_panel") and self._round2_panel is not None:
                                                    self._round2_panel.hide()
                                                    self._round2_panel.destroy()
                                                    self._round2_panel = None
                                                if hasattr(self, "_round2_overlay") and self._round2_overlay is not None:
                                                    self._round2_overlay.hide()
                                                    self._round2_overlay.destroy()
                                                    self._round2_overlay = None
                                            except Exception:
                                                pass
                                            return tk2.done
                                        base.taskMgr.doMethodLater(0.65, _r2_cleanup, "round2-cleanup")
                                        return tk0.done

                                    base.taskMgr.doMethodLater(1.2 + 2.7, _r2_start_fade_out, "round2-hold")
                                except Exception:
                                    pass
                                return tsk.done

                            base.taskMgr.doMethodLater(0.65, _post_cleanup, "post-tournament-cleanup")
                            return task.done

                        # Orchestrate timings: pre-blank, then fade-in, hold, then fade-out
                        pre_blank = 1.5   # seconds of blank screen before showing text
                        hold_after_fadein = 1.2  # seconds to hold after fade-in completes

                        def _post_begin_fade_in(task):
                            # Start fade-in now
                            base.taskMgr.add(_post_fade_in, "post-tournament-fade-in")
                            # Schedule fade-out start after fade-in + hold
                            base.taskMgr.doMethodLater(1.2 + hold_after_fadein, _post_start_fade_out, "post-tournament-hold")
                            return task.done

                        # Start the fade-in after the pre-blank delay
                        base.taskMgr.doMethodLater(pre_blank, _post_begin_fade_in, "post-tournament-preblank")
                    except Exception:
                        # On failure to show overlay, just clear UI
                        self._clear_tournament_ui()

                    return
                # Build next round matches from winners; handle bye by carrying last forward
                new_matches = []
                next_accumulator = []
                temp = list(winners)
                # Reset accumulator for subsequent round
                self.tournament_next_indices = []
                if len(temp) % 2 == 1:
                    # carry last as a bye into next accumulator
                    next_accumulator.append(temp.pop())
                # Pair remaining
                for i in range(0, len(temp), 2):
                    a = temp[i]
                    b = temp[i + 1]
                    new_matches.append({
                        "match_id": len(new_matches) + 1,
                        "a_index": a,
                        "b_index": b
                    })
                # Set new round state
                self.tournament_matches = new_matches
                self.tournament_idx = 0
                self.tournament_round = getattr(self, "tournament_round", 1) + 1
                # Seed accumulator with bye (if any)
                self.tournament_next_indices = next_accumulator
                # Proceed to next round
                self._show_batch1_tournament_match()
            else:
                # Continue current round
                self._show_batch1_tournament_match()
        except Exception as e:
            print(f"[Tournament] Record error: {e}")

    def _start_tournament_rotation(self):
        """Start rotation animation for tournament objects."""
        if not hasattr(self, 'tournament_objects') or not self.tournament_objects:
            return
        self.taskMgr.add(self._tournament_rotation_task, "tournament-rotation-task")

    def _tournament_rotation_task(self, task):
        """Rotate both tournament objects each frame."""
        try:
            speed = getattr(self, 'tournament_spin_speed', 0.8)
            if hasattr(self, 'tournament_objects'):
                for obj in self.tournament_objects:
                    try:
                        if obj:
                            obj.setH(obj.getH() + speed)
                    except Exception:
                        pass
        except Exception:
            pass
        return task.cont

    def _tint_object(self, node_path, on: bool):
        """Apply or clear a green tint on the given object NodePath."""
        try:
            if not node_path:
                return
            if on:
                node_path.setColorScale(0.6, 1.0, 0.6, 1.0)
            else:
                node_path.clearColorScale()
        except Exception:
            pass

