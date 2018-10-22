# ELOP Logstash Pipelines


## Struktur

**pipelines** -> Distributor Pattern (Filebeat,Metricbeat und Packetbeat)

**pipelines/filebeat** -> Filebeat Filter + Output

**pipelines/metricbeat** -> Metricbeat Filter + Output

**pipelines/packetbeat** -> Packetbeat Filter + Output

**pipelines/winlogbeat** -> Winlogbeat Filter + Output

**pipelines/generic** -> Generic Filter + Output

**grok** -> eigene Grok-Pattern

**pipelines.yml** -> Definition aktiver Pipelines 

**logstash.yml** -> allgemeine Konfiguration Logstash

## Pipeline anlegen

1. Pipeline mit Filter und Output im entsprechenden Verzeichnis anlegen
2. Pipeline in pipelines.yml definieren
3. Pipeline im entsprechenden Distributor Pattern aufnehmen
4. Logstash führt nach Änderungen an der Konfiguration automatisch einen Reload aus (dauerhafte Funktionalität/Stabilität ist noch zu überprüfen)


## Curator Konfiguration

- Curator wird gegenwärtig stündlich per Cronjob gestartet
- Logs finden sich unter /var/log/curator/curator.log / Logrotate ist aktiviert
- entsprechende Action unter curator/actionfiles/ anlegen oder vorhandene editieren
- curator_cron.sh führt automatisch alle defininierten Actions aus

[Wiki Curator](https://wiki.avm.de/display/IT/Curator)



## Links

[Logstash Pipelines](https://www.elastic.co/guide/en/logstash/current/multiple-pipelines.html)

[Logstash Distributor Pattern](https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html#distributor-pattern)
