require "sketchup.rb"
require "auto_rendering_plugin/models.rb"

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
        MIN_FP_HEIGHT = 420 # 35ft * 12

        # Try not to use spaces
        PANO_NAME_LOOKUP = {
          "living room" => ["living room", "living"],
          "bed 1" => ["bed1", "bed 1", "bedroom1", "bedroom 1"],
          "bed 2" => ["bed2", "bed 2", "bedroom2", "bedroom 2"],
          "bed 3" => ["bed3", "bed 3", "bedroom3", "bedroom 3"],
          "bed 4" => ["bed4", "bed 4", "bedroom4", "bedroom 4"],
          "bath 1" => ["bath1", "bath 1", "bathroom1", "bathroom 1"],
          "bath 2" => ["bath2", "bath 2", "bathroom2", "bathroom 2"],
          "bath 3" => ["bath3", "bath 3", "bathroom3", "bathroom 3"],
          "bath 4" => ["bath4", "bath 4", "bathroom4", "bathroom 4"],
          "closet 1" => ["closet1", "closet 1"],
          "closet 2" => ["closet2", "closet 2"],
          "closet 3" => ["closet3", "closet 3"],
          "closet 4" => ["closet4", "closet 4"],
          "half bath" => ["half bath", "half", "half bathroom"],
        }

        CAMERA_TARGET_RADIUS = 1000
        DEFAULT_SETTINGS_CODE = "FV000"
        DEFAULT_PANO = "Entry"

        @@current_settings_code = DEFAULT_SETTINGS_CODE
        @@current_pano_name = DEFAULT_PANO

        def self.set_settings_code(code)
          @@current_settings_code = code
        end

        def self.set_pano_name(name)
          model = Sketchup.active_model
          page = FinishVisionVR::RenderingPlugin.get_page_for_pano(name)
          if !page.nil?
            model.pages.selected_page = page
            @@current_pano_name = name
          end
        end

        # The name of the file should give us the record ID for the unit
        def self.get_unit_id
            model = Sketchup.active_model
            title = model.title || ""
            title_parts = title.split("-")
            return nil if title_parts.length == 0
            return title_parts[0].strip
        end

        def self.get_page_for_pano(name)
          return nil if name.nil? or name == ""
          model = Sketchup.active_model
          name = name.strip.downcase
          searches = FinishVisionVR::RenderingPlugin::PANO_NAME_LOOKUP[name] || [name]

          model.pages.find do |p|
            n = p.name.downcase
            !!searches.find { |s| n.include? s }
          end
        end

        def self.create_pano_scenes
          unit_id = FinishVisionVR::RenderingPlugin.get_unit_id
          u = FinishVisionVR::RenderingPlugin::Unit.find(unit_id)
          return UI.messagebox("Unit not found...") if u.nil?
          model = Sketchup.active_model
          panos = u.panos

          # Switch to "Ceiling" scene so the ceiling is on.
          ceiling_page = FinishVisionVR::RenderingPlugin.get_page_for_pano("Ceiling")
          model.pages.selected_page = ceiling_page unless ceiling_page.nil?

          panos.each do |p|
            exists = FinishVisionVR::RenderingPlugin.get_page_for_pano(p["Name"])
            next unless exists.nil?

            page = model.pages.add(p["Name"])

            if !p["Scene Camera Target Vector"].nil?
              x = p["Scene Camera X"]
              y = p["Scene Camera Y"]
              z = p["Scene Camera Z"]
              eye = [x.m, y.m, z.m]
              target = JSON.parse(p["Scene Camera Target Vector"]) || [1,0,0]
              up = [0,0,1]

              page.use_camera = false
              page.camera.set(eye, target, up)
              page.update(1)
              page.use_camera = true
            end
          end
        end

        def self.create_pano_scenes_with_direction
          unit_id = FinishVisionVR::RenderingPlugin.get_unit_id
          u = FinishVisionVR::RenderingPlugin::Unit.find(unit_id)
          return UI.messagebox("Unit not found...") if u.nil?
          model = Sketchup.active_model
          panos = u.panos

          # Switch to "Ceiling" scene so the ceiling is on.
          ceiling_page = FinishVisionVR::RenderingPlugin.get_page_for_pano("Ceiling")
          model.pages.selected_page = ceiling_page unless ceiling_page.nil?

          panos.each do |p|
            page = FinishVisionVR::RenderingPlugin.get_page_for_pano(p["Name"])
            page = model.pages.add(p["Name"]) if page.nil?

            x = p["Scene Camera X"]
            y = p["Scene Camera Y"]
            z = p["Scene Camera Z"]
            eye = [x.m, y.m, z.m]
            angle = p["Scene Camera Angle"]
            angle = 0 if angle.nil?
            target_x = Math.cos(angle * Math::PI / 180) * CAMERA_TARGET_RADIUS
            target_y = Math.sin(angle * Math::PI / 180) * CAMERA_TARGET_RADIUS
            target = [target_x, target_y, z.m]
            up = [0,0,1]

            page.use_camera = false
            page.camera.set(eye, target, up)
            page.update(1)
            page.use_camera = true
          end
        end

        # Goes through each view and updates the camera locations in Airtables
        def self.update_camera_locations
            unit_id = FinishVisionVR::RenderingPlugin.get_unit_id
            u = FinishVisionVR::RenderingPlugin::Unit.find(unit_id)
            return UI.messagebox("Unit not found...") if u.nil?
            panos = u.panos

            model = Sketchup.active_model
            pano_pages = []

            # Switch to "Entry" page since there should always be an entry
            entry_page = FinishVisionVR::RenderingPlugin.get_page_for_pano("Entry")
            model.pages.selected_page = entry_page unless entry_page.nil?

            # Turn off scene transition times
            model.options["PageOptions"]["TransitionTime"] = 0

            panos.each do |pano|
              p = FinishVisionVR::RenderingPlugin.get_page_for_pano(pano["Name"])
              next if p.nil?

              pano_pages << p
              eye = p.camera.eye
              target = p.camera.target
              up = p.camera.up
              x = eye[0].to_m
              y = eye[1].to_m
              z = eye[2].to_m

              pano["Scene Camera X"] = x
              pano["Scene Camera Y"] = y
              pano["Scene Camera Z"] = z
              pano["Scene Camera Target Vector"] = target.to_a.to_s
              pano.save
            end

            # Remove pages that we don't want to render
            pages_to_remove = model.pages.select { |p| !pano_pages.include?(p) }
            pages_to_remove.each { |r| model.pages.erase r }
        end

        def self.set_floor_plan_geolocation
            model = Sketchup.active_model
            shadowinfo = model.shadow_info

            #Set lat and long to 0, 0 for better sun positioning
            shadowinfo["Latitude"] = 20.0
            shadowinfo["Longitude"] = 0.0
            shadowinfo["Country"] = "USA"
            shadowinfo["City"] = "Springfield (MO)"
            shadowinfo["TZOffset"] = 0.0
            shadowinfo["ShadowTime"] = Time.new(2019,8,20, 12,30,0, "+00:00")
        end

        # Sets the geolocation to 0,0.  Nothing particular to floor plan now.
        def self.set_pano_geolocation
            model = Sketchup.active_model
            shadowinfo = model.shadow_info

            #Set lat and long to 0, 0 for better sun positioning
            shadowinfo["Latitude"] = 20.0
            shadowinfo["Longitude"] = 0.0
            shadowinfo["Country"] = "USA"
            shadowinfo["City"] = "Springfield (MO)"
            shadowinfo["TZOffset"] = 0.0
            shadowinfo["ShadowTime"] = Time.new(2019,11,1, 13,30,0, "+00:00")
        end


        def self.floor_plan_camera
          model = Sketchup.active_model
           # Disable transition time
           model.pages.each { |p| p.transition_time = 0 }
           floor_plan_page = model.pages.find { |p| p.name.include? "Floor Plan" }

           if !floor_plan_page.nil?
             UI.start_timer(4) {
               model.pages.selected_page = floor_plan_page
             }
           end

           walls = []
           Sketchup.active_model.entities.each do |e|
             next if e.hidden?
             sum = 0
             sum = sum + 1 if e.bounds.width > 12
             sum = sum + 1 if e.bounds.height > 12
             sum = sum + 1 if e.bounds.depth > 12
             # Make sure at least 2 sides are greater than a foot. Ignore tiny objects.
             next if sum < 2

             walls << e
           end

           # Create a virtual bounding box
           bbox = Geom::BoundingBox.new
           walls.each { |ent| bbox.add(ent.bounds) rescue nil }
           # Get the bottom front left corner as a Geom::Point3d
           # Use Ruby's multiple assignment
           x, y, z = bbox.center.to_a
           w = bbox.width
           h = bbox.height
           d = bbox.depth

           # Enscape default FOV
           fov = 90.0
           width = w.to_f
           height = h.to_f
           target_width = height * 1.7777

           # Factor in minimum height
           camera_height = [target_width/(2*Math.tan(fov/2*Math::PI/180))+30+z, FinishVisionVR::RenderingPlugin::MIN_FP_HEIGHT].max

           center_x = x
           center_y = y
           eye_x = center_x
           eye_y = center_y-50

           eye = [eye_x,eye_y,camera_height]
           target = [center_x,center_y,0]
           up = [0,1,0]
           my_camera = Sketchup::Camera.new eye, target, up
           my_camera.fov = fov

           UI.start_timer(8) {
             # Get a handle to the current view and change its camera.
             view = Sketchup.active_model.active_view
             view.camera = my_camera
           }
        end

        def self.move_to_enscape_view
          model = Sketchup.active_model

          # Turn off scene transition times
          model.pages.each { |p| p.transition_time = 0 }
          model.options["PageOptions"]["TransitionTime"] = 0

          page = model.pages.find { |p| p.name.downcase.include? "enscape" }
          model.pages.selected_page = page unless page.nil?
        end

        def self.setup_screenshot_rendering
          model = Sketchup.active_model
          non_screenshot_pages = model.pages.select do |p|
            # Only pages named Enscape View are screenshots
            next true if !p.name.downcase.include?("enscape")

            result = /[fF][vV]\d{3}/.match(p.name)
            if result.nil?
              settings_codes = [DEFAULT_SETTINGS_CODE]
            else
              settings_codes = result.to_a
            end

            next !settings_codes.include?(@@current_settings_code)
          end

          # Switch to an Enscape View and remove non screenshot views
          screenshot_view = model.pages.find { |p| !non_screenshot_pages.include?(p.name) }
          model.pages.selected_page = screenshot_view unless screenshot_view.nil?
          non_screenshot_pages.each { |s| model.pages.erase(s) }
        end

        def self.init_ui
            tools_menu = UI.menu("Tools")
            finish_vision_menu = tools_menu.add_submenu("FinishVisionVR")
            finish_vision_menu.add_item("Floor Plan Camera") {
                FinishVisionVR::RenderingPlugin.floor_plan_camera
            }
            finish_vision_menu.add_item("Set Geolocation (Floor Plan)") {
                FinishVisionVR::RenderingPlugin.set_floor_plan_geolocation
            }
            finish_vision_menu.add_item("Set Geolocation (Panorama)") {
                FinishVisionVR::RenderingPlugin.set_pano_geolocation
            }
            finish_vision_menu.add_item("Update Camera Locations") {
                FinishVisionVR::RenderingPlugin.update_camera_locations
            }
            finish_vision_menu.add_item("Setup Screenshot Rendering") {
                FinishVisionVR::RenderingPlugin.setup_screenshot_rendering
            }
            finish_vision_menu.add_item("Create Pano Scenes") {
                FinishVisionVR::RenderingPlugin.create_pano_scenes
            }
            finish_vision_menu.add_item("Create Pano Scenes w/ Direction") {
                FinishVisionVR::RenderingPlugin.create_pano_scenes_with_direction
            }
        end


        if !file_loaded?(__FILE__)
            FinishVisionVR::RenderingPlugin.init_ui
            file_loaded(__FILE__)
        end
    end
end

