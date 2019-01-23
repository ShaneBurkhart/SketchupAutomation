require "sketchup.rb"
require 'extensions.rb'

module FinishVisionVR
    module DrawingPlugin
        def self.install_gems
            Gem.install "airrecord"
        end

        if !file_loaded?(__FILE__)
            FinishVisionVR::RenderingPlugin.install_gems
            require "secrets.rb"

            ex = SketchupExtension.new('FinishVisionVR - Drawing', 'drawing_plugin/main')
            ex.description = 'SketchUp Ruby API example creating a custom tool.'
            ex.version     = '1.0.0'
            ex.copyright   = 'Trimble Navigations © 2016'
            ex.creator     = 'SketchUp'

            Sketchup.register_extension(ex, true)

            file_loaded(__FILE__)
        end
    end
end
