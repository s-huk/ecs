# encoding: utf-8
require 'logstash/devutils/rspec/spec_helper'

# #### START
# https://github.com/colinsurprenant/logstash-input-syslog/blob/906337b030e9563c8c23f6b4f44c0ad2f08a4fbc/spec/inputs/syslog_spec.rb#L18
# running the grok code outside a logstash package means
# LOGSTASH_HOME will not be defined, so let's set it here
# before requiring the grok filter
#
unless LogStash::Environment.const_defined?(:LOGSTASH_HOME)
  LogStash::Environment::LOGSTASH_HOME = File.expand_path('../../', __FILE__)
end

# temporary fix to have the spec pass for an urgen mass-publish requirement.
# cut & pasted from the same tmp fix in the grok spec
# see https://github.com/logstash-plugins/logstash-filter-grok/issues/72
# this needs to be refactored and properly fixed
module LogStash::Environment
  # also :pattern_path method must exist so we define it too
  unless method_defined?(:pattern_path)
    def pattern_path(path)
      ::File.join(LOGSTASH_HOME, 'patterns', path)
    end
  end
end
# #### END

require 'logstash/plugin'
require 'logstash/inputs/syslog'
require 'logstash/filters/grok'
require 'json'
require 'diffy' #require_relative 'logstash/vendor/jruby/lib/ruby/gems/shared/gems/diffy-3.2.1/lib/diffy'

def compare_json(json1, json2)
	if(json1.is_a?(Array) && json2.is_a?(Array) && json1.count == json2.count) 
		json1.each_with_index do |obj, index|
			json1_obj, json2_obj = obj, json2[index]
			result = compare_json(json1_obj, json2_obj)
			return false if result == false
		end
	elsif(json1.is_a?(Hash) && json2.is_a?(Hash) && json1.count == json2.count)
		json1.each do |key,value|
			return false unless json2.has_key?(key) and compare_json(value, json2[key])		
		end
	else 
		return false if not json1 == json2
	end
	return true
end


def order_json(json1)
	if json1.is_a?(Array)
		newArray = Array.new
		json1.each_with_index {|val, i| newArray[i] = order_json(val) }
		return newArray
	elsif json1.is_a?(Hash)
		newHash = Hash.new
		json1.each {|key, val| newHash[key] = order_json(val) }
		return newHash.class[newHash.sort {|x, y| x[0].to_s <=> y[0].to_s } ]
	else
		return json1
	end
end

def withdraw_comments(json_lines)
	resJson = ""
	# Kommentare zeilenweise herausfiltern - Matching von Quotings mit Hilfe von Lookbehind: +((?<![\\])['"])((?:.(?!(?<![\\])\2))*.?)\2
	json_lines.each_line do |line|
		if line =~ /^((((?<![\\])['"])(?:.(?!(?<![\\])\3))*.?\3|[A-Za-z0-9,.: \t}{\[\]]*+)+)(\#.*)?$/
			next if $1 == nil # $1 = JSON-Zeile ohne Kommentar  $4 = Kommentar 
			resJson += $1
		else 
			resJson += line
		end
	end	
	return resJson
end


puts

Dir["../../"+ENV["LOGSTASH_TESTING_CONF_PATTERN"]].each { |conf_path|
    next unless conf_path.end_with?(".conf")
    relative_path_prefix = conf_path.chomp('.conf').sub(/^\.\.\/\.\.\//, '')

    puts "DISCOVERED FILTER CONFIG FILE: "+relative_path_prefix+".conf"
	Dir["../../"+ENV["LOGSTASH_TESTING_TESTBUNDLE_DIR"]+"/"+relative_path_prefix+"_*in.json"].each { |in_path|
        puts "  |->DISCOVERED JSON INPUT FILE: "+in_path.sub(/^\.\.\/\.\.\//, '')
		file_id = ""
		if in_path =~ /^.*#{relative_path_prefix}_(.*)in.json$/im
			file_id = $1
		end
		describe "test filter conf: "+relative_path_prefix+"_"+file_id do
			file = File.open(conf_path, 'rb')
			fileLines = file.read
			file.close

			if fileLines =~ /^.*\n[ \t]*(filter[ \t]*{.*)\n[ \t]*output[ \t]*{.*$/im   # i:ignore case, m:match all characters esp. \n
				flines = "input { stdin { codec => json } }\n"+$1+"\n\n"
			else
				raise "filter file parse failure"
			end

			config flines

			fileJson = File.open(in_path, "rb")
			json_in_kafka = JSON.parse(fileJson.read)
			fileJson.close

			sample json_in_kafka do # subject.class ist LogStash::Event
				#insist { subject.get('test') } == ('testwert')
                if File.file?("../../"+ENV["LOGSTASH_TESTING_TESTBUNDLE_DIR"]+"/"+relative_path_prefix+"_"+file_id+"must.json")
                    fileJson = File.open("../../"+ENV["LOGSTASH_TESTING_TESTBUNDLE_DIR"]+"/"+relative_path_prefix+"_"+file_id+"must.json", "rb")
					#strJson = fileJson.read
					strJson = withdraw_comments(fileJson.read)
					json_must = JSON.parse(strJson)
					fileJson.close
				else
					json_must = JSON.parse("{}")
				end
				
				json_result = JSON.parse( subject.to_json )
				if not compare_json(json_result, json_must)
					puts "\n\n######################\nFilter-Konfiguration:\n######################\n"+flines
					pretty_must = JSON.pretty_generate( order_json(json_must) )
					pretty_result = JSON.pretty_generate( order_json(json_result) )
					if compare_json(JSON.parse("{}"), json_must)
						puts "\n\n++++++++++++++++++++++++++++++++++++++\nErgebnis:\n++++++++++++++++++++++++++++++++++++++\n"
						puts pretty_result+"\n\n"
					else
						puts "\n\n++++++++++++++++++++++++++++++++++++++\nErgebnis inkl. erwarteter Anpassungen:\n++++++++++++++++++++++++++++++++++++++\n"
						puts Diffy::Diff.new(pretty_result, pretty_must) .to_s(:color)+"\n\n"
						expect( compare_json(json_result, json_must) ).to be true
					end
				end 
				
				#    File.open(Dir.pwd + "/../bundle01/fail2ban_result.json","w") do |f|
				#        f.write(JSON.pretty_generate(json_result))
				#    end
			end
		end
	}
}
  
puts












