require "sketchup.rb"
require 'extensions.rb'

module FinishVisionVR
    module RenderingPlugin
        if !file_loaded?(__FILE__)
            ex = SketchupExtension.new('FinishVisionVR - Auto Rendering', 'auto_rendering_plugin/main')
            ex.description = 'SketchUp Ruby API example creating a custom tool.'
            ex.version     = '1.0.0'
            ex.copyright   = 'Trimble Navigations © 2016'
            ex.creator     = 'SketchUp'

            Sketchup.register_extension(ex, true)

            file_loaded(__FILE__)
        end
    end
end
