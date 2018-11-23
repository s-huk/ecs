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

## Pipeline testen
**Testumgebung initialisieren, Tests starten, Hilfe anzeigen**: `./run-testbundle.sh`

**Beispiel:** `./run-testbundle.sh bundle01` (siehe Hilfe)

Jede selektierte Konfiguration (d.h. Conf-File) wird mit jedem namensgleichen JSON-Input-File des angegebenen Testbundles getestet. Konfigurationen ohne passendes JSON-Input-File werden nicht getestet. Optional kann zu jedem JSON-Input-File ein JSON-Must-File (erwarteter Logstash-Output) hinterlegt werden (siehe Beispiele in `testing/bundle01`). 

Benennungsmuster der JSON-Dateien: 

- JSON-Input: <conf_filename_ohne_extension>_{optionaler_test_identifier}in.json
- JSON-Erwartung: <conf_filename_ohne_extension>_{optionaler_test_identifier}must.json

Conf- und JSON-Files werden als zueinander passend betrachtet und getestet, wenn der Base-Filename (d.h. conf_filename_ohne_extension) und auch der relative Pfad zum jeweiligen `pipelines`-Ordner gleich sind.

## Curator Konfiguration

- Curator wird gegenwärtig stündlich per Cronjob gestartet
- Logs finden sich unter /var/log/curator/curator.log / Logrotate ist aktiviert
- entsprechende Action unter curator/actionfiles/ anlegen oder vorhandene editieren
- curator_cron.sh führt automatisch alle defininierten Actions aus

[Wiki Curator](https://wiki.avm.de/display/IT/Curator)



## Links

[Logstash Pipelines](https://www.elastic.co/guide/en/logstash/current/multiple-pipelines.html)

[Logstash Distributor Pattern](https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html#distributor-pattern)
