require "airrecord"

if !file_loaded?(__FILE__)
    # Workaround for net-http-persistent lib not working on windows.
    # The RLIMIT_NOFILE isn't defined and getrlimit() throws unimplemented on machine error
    # We are overriding to end up with DEFAULT_POOL_SIZE = 256 in Net::HTTP:Persistent
    if Gem.win_platform?
        module Process
            RLIMIT_NOFILE = "foo"

            # Normally returns an array of two values [low_val, high_val]
            def self.getrlimit(arg)
                return [256*4]
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
