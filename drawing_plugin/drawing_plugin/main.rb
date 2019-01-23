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
            UI.messagebox("Handler loaded")
        end

        def onFailure(error_message)
            self.error = error_message
            Sketchup::set_status_text('')
            UI.messagebox(error_message)
        end
    end

    module DrawingPlugin
        COMPONENT_SEARCH_URL = "http://construction-vr.shaneburkhart.com/93e8e03a-9c36-48bc-af15-54db7715ac15/component/search"

        def self.open_component_search
            dialog = UI::HtmlDialog.new(
                width: 300,
                height: 600,
            )
            dialog.set_url COMPONENT_SEARCH_URL
            dialog.add_action_callback("add_to_model") { |action_context, url|
                dialog.close
                FinishVisionVR::DrawingPlugin.place_component(url)
            }
            dialog.show
        end

        def self.place_component(url)
            model = Sketchup.active_model
            comp = model.definitions.load_from_url(url, FinishVisionVR::ComponentLoadHandler.new(url))
            UI.messagebox("Loaded")
            return if comp.nil?
            UI.messagebox("Place that")
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
