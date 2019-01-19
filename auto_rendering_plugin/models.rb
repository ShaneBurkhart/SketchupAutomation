require "airrecord"

if !file_loaded?(__FILE__)
    # Workaround for airrecord net-http lib to work on Windows
    if Gem.win_platform?
        module Airrecord
            class Client
                old_fn = instance_method(:connection)

                define_method(:connection) do
                    old_fn.bind(self).()
                    Net::HTTP::Persistent.const_set("DEFAULT_POOL_SIZE", 256)
                end
            end
        end
    end
    file_loaded(__FILE__)
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
