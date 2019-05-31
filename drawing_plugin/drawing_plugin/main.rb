require "sketchup.rb"
require "cgi"

module FinishVisionVR
    class ComponentLoadHandler
        attr_accessor :error, :url

        def initialize(url)
            self.url = url
        end

        def onPercentChange(percent)
            Sketchup::set_status_text("LOADING: #{percent}%")
        end

        def cancelled?
            return false
        end

        def onSuccess
            Sketchup::set_status_text('')
        end

        def onFailure(error_message)
            self.error = error_message
            Sketchup::set_status_text('')
            UI.messagebox(error_message)
        end
    end

    module DrawingPlugin
        COMPONENT_SEARCH_URL = "http://construction-vr.shaneburkhart.com/93e8e03a-9c36-48bc-af15-54db7715ac15/component/search"
        @@is_loading_component = false

        # The name of the file should give us the record ID for the unit
        def self.get_unit_id
            model = Sketchup.active_model
            title = model.title || ""
            title_parts = title.split("-")
            return nil if title_parts.length == 0
            return title_parts[0].strip
        end

        def self.open_component_search
            unit_id = FinishVisionVR::DrawingPlugin.get_unit_id
            return if unit_id.nil?

            dialog = UI::HtmlDialog.new(
                width: 900,
                height: 600,
            )
            dialog.set_url "#{COMPONENT_SEARCH_URL}?unit_id=#{unit_id}"
            dialog.add_action_callback("add_to_model") { |action_context, url, type|
                next if @@is_loading_component
                @@is_loading_component = true

                UI.start_timer(1.0, false) {
                    model = Sketchup.active_model
                    model.select_tool('SelectionTool')
                    comp = FinishVisionVR::DrawingPlugin.load_component(url)

                    model.select_tool('SelectionTool')
                    FinishVisionVR::DrawingPlugin.place_component(comp)
                    @@is_loading_component = false
                }
            }
            dialog.show
        end

        def self.load_component(url)
          model = Sketchup.active_model
          comp = model.definitions.load_from_url(url, FinishVisionVR::ComponentLoadHandler.new(url))
        end

        def self.place_component(comp)
            return if comp.nil?
            Sketchup.active_model.place_component(comp)
        end

        def self.init_ui
            tools_menu = UI.menu("Tools")
            finish_vision_menu = tools_menu.add_submenu("FinishVisionVR - Drawing")
            finish_vision_menu.add_item("Component Search") {
                FinishVisionVR::DrawingPlugin.open_component_search
            }
        end

        if !file_loaded?(__FILE__)
            FinishVisionVR::DrawingPlugin.init_ui
            file_loaded(__FILE__)
        end
    end
end
