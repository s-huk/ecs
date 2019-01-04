# ELOP Logstash Pipelines

Dieses Repository beinhaltet alle Quellen und Tools für Logstash-Pipelines der **Elastic for Operations** Systeme.


## Struktur

#### Logstash

**[logstash.yml](logstash.yml)** -> Allgemeine Logstash-Konfiguration

**[pipelines.yml](pipelines.yml)** -> Zentrale [Multi-Pipeline](https://www.elastic.co/guide/en/logstash/current/multiple-pipelines.html)-Konfiguration.

**[pipelines](pipelines/)** -> Die Orchestration der Pipelines mittels [Distributor Pattern](https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html#distributor-pattern).

**[grok](grok/)** -> Eigene Grok-Patterns

#### Testing

**[testing](testing/)** -> Alle Tests und Utilities für das Aufsetzen und Testen der Logstash Pipelines.

#### Curator

**[curator](curator/)** -> Alle Konfigs für den [Wiki Curator](https://wiki.avm.de/display/IT/Curator).

#### Dokumentation

**[doc](doc/)** -> Assets zur Dokumentation der Pipelines und des verwendeten Schemas.


## Projekt Anpassungen

Wenn Anpassungen am Projekt vorgenommen werden müssen, kann das lokal vorbereitet und getestet werden.

#### Setup

Einmalig müssen mittels `make setup` Abhängigkeiten für den [Kafka Consumer](run-kafka-consumer.sh) und die [Logstash Testumgebung](run-testbundle.sh) initialisiert werden.

#### Pipeline anlegen

1. Pipeline mit Filter und Output im entsprechenden Verzeichnis anlegen
2. Pipeline in pipelines.yml definieren
3. Pipeline im entsprechenden Distributor Pattern aufnehmen
4. Pipeline testen (siehe nächster Abschnitt).
5. git Commit erstellen, nach gitlab pushen und mittels eine Merge-Requests in master-Branch mergen.
6. Nachdem der Merge-Request submitted wurde, läuft das [Deplyoment der Konfiguration ins Staging-System via Jenkins](https://jenkins.avm.de/job/elastic/job/logstash-config-sync-stage/).

#### Pipeline testen

- **Hilfe anzeigen:** `./run-testbundle.sh -h`
- **Tests starten:** `./run-testbundle.sh` <br>
(testet jede Conf in pipelines/\*/\*.conf gegen passenden JSON-Input in testing/pipelines/\*/\*.json)
- **Zu testende Confs explizit angeben:** `./run-testbundle.sh pipelines/*/ha*.conf` (siehe Hilfe)
- **Samples aus Kafka lesen:** `./run-kafka-consumer.sh` liest aus Kafka ein, z.B. `./run-kafka-consumer.sh --topic ops_filebeat`. Genaue Verwendung siehe `./run-kafka-consumer.sh -h`.

Jede selektierte Konfiguration (d.h. Conf-File) wird mit jedem namensgleichen JSON-Input-File in testing/pipelines getestet. Konfigurationen ohne passendes JSON-Input-File werden nicht getestet. Es ist vorgesehen, zu jedem JSON-Input-File ein JSON-Must-File (erwarteter Logstash-Output) zu hinterlegen (siehe Beispiele in testing/pipelines).

Benennungsmuster der JSON-Dateien:

- JSON-Input: <conf_filename_ohne_extension>_{optionaler_test_identifier}_in.json
- JSON-Erwartung: <conf_filename_ohne_extension>_{optionaler_test_identifier}_must.json

Conf- und JSON-Files werden als zueinander passend betrachtet und getestet, wenn der Base-Filename (d.h. conf_filename_ohne_extension) und auch der relative Pfad zum jeweiligen pipelines-Ordner gleich sind.

#### Dokumentation aktualisieren (experimental)

Nach dem Verändern von Pipelines sollte stets die Dokumentation (diese README.md) generiert und ins mit ins git eingecheckt werden werden. Die Generierung der README-Dokumentation geschieht mittels `./run-doc-generation.sh`

#### Mapping generieren (experimental)

Beispiel: `./run-template-tools.sh pipelines/reporting-backend-service/*.conf`

Jedes Feld innerhalb aller zur Pipeline gehörigen Must-Dateien (JSON-Erwartungen) wird gemäß zugrunde liegender Schema-Definition automatisch in das Mapping übernommen, sofern auch eine Schema-Definition für dieses Feld vorliegt (d.h. sofern das Feld nicht verwaist ist). Alle benötigten Felder müssen also entweder Schema-treu benannt und durch Testfälle (MUST-Dateien) abgedeckt sein - oder alternativ manuell in das ensprechenden Mapping-Template (also die JSON-Datei neben dem Conf-File) eingetragen werden.

##### Konsolen-Vorschau der Zuordnung aller erwarteten Felder (d.h. Felder aus MUST-Files) in die gegebene Schema-Definition:

`./run-stat.sh pipelines/reporting-backend-service/fw-reports.conf`


#### Curator Konfiguration

- Curator wird gegenwärtig stündlich per Cronjob gestartet
- Logs finden sich unter /var/log/curator/curator.log / Logrotate ist aktiviert
- entsprechende Action unter curator/actionfiles/ anlegen oder vorhandene editieren
- curator_cron.sh führt automatisch alle defininierten Actions aus

[Wiki Curator](https://wiki.avm.de/display/IT/Curator)

