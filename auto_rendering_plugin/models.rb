require "airrecord"

# Workaround for airrecord net-http lib to work on Windows
if Gem.win_platform?
    Net::HTTP::Persistent.const_set("DEFAULT_POOL_SIZE", 256)
end

module FinishVisionVR
    module RenderingPlugin
        class Unit < Airrecord::Table
            self.base_key = FinishVisionVR::RenderingPlugin::AIRTABLE_RENDERING_APP_ID
            self.table_name = "Units"

            def panos
                if @panos.nil?
                    @panos = FinishVisionVR::RenderingPlugin::Pano.all(filter: "(FIND(\"#{self.id}\", ARRAYJOIN({Unit ID})))", sort: { "Order Priority": "asc" }) || []
                end

                return @panos
            end
        end

        class Pano < Airrecord::Table
            self.base_key = FinishVisionVR::RenderingPlugin::AIRTABLE_RENDERING_APP_ID
            self.table_name = "Panos"

            def unit
                if @unit.nil?
                    @unit = FinishVisionVR::RenderingPlugin::Unit.all(filter: "(FIND(\"#{self.id}\", {Pano IDs}))").first
                end

                return @unit
            end
        end
    end
end
