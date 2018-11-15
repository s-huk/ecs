# encoding: utf-8
require 'logstash/devutils/rspec/spec_helper'

# #### START
# https://github.com/colinsurprenant/logstash-input-syslog/blob/906337b030e9563c8c23f6b4f44c0ad2f08a4fbc/spec/inputs/syslog_spec.rb#L18
# running the grok code outside a logstash package means
# LOGSTASH_HOME will not be defined, so let's set it here
# before requiring the grok filter
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


# Abwandlung von Quelle:  https://gist.github.com/binarydev/aeb35977a2ad22eeaea1 (code wurde auf Korrektheit geprueft)
def compare_json(json1, json2)
  result = false

  # Typumwandlung nach JSON
  unless((json1.class == json2.class) && (json1.is_a?(String) || json1.is_a?(Hash) || json1.is_a?(Array))) 
    return false
  end
  json1,json2 = [json1,json2].map! do |json|
    json.is_a?(String) ? JSON.parse(json) : json
  end

  # Pruefung auf Gleichheit (rekursiv)
  if(json1.is_a?(Array))
    json1.each_with_index do |obj, index|
      json1_obj, json2_obj = obj, json2[index]
      result = compare_json(json1_obj, json2_obj)
      break unless result
    end
  elsif(json1.is_a?(Hash))
    json1.each do |key,value|
      return false unless json2.has_key?(key)
      json1_val, json2_val = value, json2[key]
      if(json1_val.is_a?(Array) || json1_val.is_a?(Hash))
        result = compare_json(json1_val, json2_val)
      else
        result = (json1_val == json2_val)
      end
      break if result == false
    end
  end

  return result ? true : false
end


describe 'simple syslog line' do
  file = File.open(Dir.pwd + "/../../pipelines/filebeat/fail2ban-legacy.conf", 'rb')
  allLines = file.read
  file.close
  
  if allLines =~ /^.*(?<flines>filter.*)output.*$/im   # i:ignore case, m:match all characters esp. \n
      flines = "input { stdin { codec => json } }\n"+$1+"\n\n"
  else 
      raise "grok parse failure"
  end 
  puts "\n\n######################\nFilter-Konfiguration:\n######################\n"+flines
  config flines
    
#   config <<-CONFIG
#     filter {
#       ...  
#     }
#   CONFIG
  

  fileJson = File.open(Dir.pwd + "/../bundle01/fail2ban_in.json", "rb")
  str_json_in_kafka = fileJson.read
  json_in_kafka = JSON.parse(str_json_in_kafka)
  fileJson.close

  fileJson = File.open(Dir.pwd + "/../bundle01/fail2ban_must.json", "rb")
  json_must = JSON.parse(fileJson.read)
  fileJson.close
  
  sample json_in_kafka do
    #insist { subject.get('test') } == ('testwert')
    # subject.class ist LogStash::Event
    json_result = JSON.parse( subject.to_json )
    puts "\n\n======================\nLogstash-Ergebnis:\n======================\n"+JSON.pretty_generate(json_result)
    puts "\n\n***********************\nLogstash-Erwartung:\n***********************\n"+JSON.pretty_generate(json_must)
    expect( compare_json(json_result, json_must) ).to be true
#    File.open(Dir.pwd + "/../bundle01/fail2ban_result.json","w") do |f|
#        f.write(JSON.pretty_generate(json_result))
#    end
  end

end











