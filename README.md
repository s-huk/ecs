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

## Links

[Logstash Pipelines](https://www.elastic.co/guide/en/logstash/current/multiple-pipelines.html)

[Logstash Distributor Pattern](https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html#distributor-pattern)
