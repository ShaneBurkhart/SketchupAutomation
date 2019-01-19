require "sketchup.rb"

# TODO Pos floor plan camera
# TODO Sync view camera positions with Airtable
# TODO Set time of day and geolocation
# TODO Create keybindings for commands

# RENDERING PROCESS
# 1. File is submitted with appropriate formatting
#       - Scenes need to be labeled & created in the correct places per plans
#       - The unit needs to be placed on the origin per plans
#       - Make sure there is a "Floor Plan" view no ceiling or ceiling lights
#       - Entire unit is one component
# 2. File is sent to Rendering Computer and is opened
#       - Rename file to "<Unit ID>"
#       - Update Airtable pano locations with the camera coords of each page
#           - Get the name from the page name
#       - Loop through all pages until we hit the same camera coords
#       - Go through panorama files and save image with appropriate name
#           - Based on camera position matching
#       - Upload files to Airtables
#
# SketchUp Extension
# - Create menu commands that can be mapped to keybindings
# - Bind to keys that match the Python AutoGUI buttons
#       - Set geolocation
#       - Set time of day for panos
#       - Set time of day for "Floor Plan" page
#
# Python AutoGUI
# - Open the file in SketchUp
# - Start Enscape
# - Update Enscape settings for floor plan. Remove when done.
# - Go to "Floor Plan" view and render
#       - Set camera location
#       - Time of day
# - Update Enscape settings for pano. Remove when done.
# - Use keybindings to loop through pages and render panos
#       - Set camera location
#       - Time of day
#       - Until pano is same camera location
# - Loop through panos that were rendered and save them
# - Add to Airtable

module FinishVisionVR
    module RenderingPlugin
        # The name of the file should give us the
        def self.get_unit_id

        end
        # Goes through each view and updates the camera locations in Airtables
        def self.update_camera_locations
            model = Sketchup.active_model
            model.pages.each do |p|
                eye = p.camera.eye
                x = eye[0]
                y = eye[1]
                z = eye[2]
            end
        end

        # Sets the geolocation to 0,0.  Nothing particular to floor plan now.
        def self.set_floor_plan_geolocation
            model = Sketchup.active_model
            shadowinfo = model.shadow_info

            #Set lat and long to 0, 0 for better sun positioning
            shadowinfo["Latitude"] = 0
            shadowinfo["Longitude"] = 0
            shadowinfo["Country"] = "USA"
            shadowinfo["Location"] = "Springfield (MO)"

            key = "GeoReference"
            # Need to set these attrs too for the geo location to take effect
            model.set_attribute(key, "GeoReferenceNorthAngle", 0.00043673960860657465)
            model.set_attribute(key, "Latitude", 0.0)
            model.set_attribute(key, "Longitude", 0.0)
            model.set_attribute(key, "LocationSource", "Manual")
            model.set_attribute(key, "ModelTranslationX", -6536277.29052482)
            model.set_attribute(key, "ModelTranslationY", -0.0)
            model.set_attribute(key, "UsesGeoReferencing", true)
        end


        def self.floor_plan_camera_for_selection
            model = Sketchup.active_model
            selection = model.selection

            if selection.empty?
                UI.messagebox("Please select the components you want a floor plan of.")
                return
            end

            # Create a virtual bounding box
            bbox = Geom::BoundingBox.new
            # For each entity in the selection array, ...
            #  add to it the bounding box of each entity
            selection.each { |ent| bbox.add(ent.bounds) rescue nil }
            # Get the bottom front left corner as a Geom::Point3d
            origin = bbox.corner(0)
            # Use Ruby's multiple assignment
            x, y, z = origin.to_a
            w = bbox.width
            h = bbox.height
            d = bbox.depth

            # Enscape default FOV
            fov = 42.0
            width = w.to_f
            height = h.to_f
            aspect_ratio = width / height
            target_width = width

            # 16/9 = 1.777777
            if aspect_ratio < 1.777777
                target_width = height * 1.77777
            end

            # Add 120 for wall height
            camera_height = target_width/(2*Math.tan(fov/2*Math::PI/180))+120+z

            center_x = x+width/2
            center_y = y+height/2
            eye_x = center_x
            eye_y = center_y-200

            eye = [eye_x,eye_y,camera_height]
            target = [center_x,center_y,0]
            up = [0,1,0]
            my_camera = Sketchup::Camera.new eye, target, up
            my_camera.fov = fov

            # Get a handle to the current view and change its camera.
            view = Sketchup.active_model.active_view
            view.camera = my_camera
        end

        def self.init_ui
            tools_menu = UI.menu("Tools")
            finish_vision_menu = tools_menu.add_submenu("FinishVisionVR")
            finish_vision_menu.add_item("Floor Plan Camera") {
                FinishVisionVR::RenderingPlugin.floor_plan_camera_for_selection
            }
            finish_vision_menu.add_item("Set Geolocation") {
                FinishVisionVR::RenderingPlugin.set_floor_plan_geolocation
            }
            finish_vision_menu.add_item("Update Camera Locations") {
                FinishVisionVR::RenderingPlugin.update_camera_locations
            }
        end


        if !file_loaded?(__FILE__)
            FinishVisionVR::RenderingPlugin.init_ui
            file_loaded(__FILE__)
        end
    end
end

