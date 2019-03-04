# ELOP Logstash Pipelines

Dieses Repository beinhaltet alle Quellen und Tools für Logstash-Pipelines der **Elastic for Operations** Systeme.


## Struktur

#### Logstash

**[logstash.yml](logstash.yml)** -> Allgemeine Logstash-Konfiguration

**[pipelines.yml](pipelines.yml)** -> Zentrale [Multi-Pipeline](https://www.elastic.co/guide/en/logstash/current/multiple-pipelines.html)-Konfiguration.

**[pipelines](pipelines/)** -> Die Orchestration der Pipelines mittels [Distributor Pattern](https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html#distributor-pattern).

**[grok](grok/)** -> Eigene Grok-Patterns

#### Testing

**[testing](testing/)** -> Logstash-Testdaten nach Pipelines (d.h. je Pipeline die Inputs inkl. Must-Vorgabe).

#### Curator

**[curator](curator/)** -> Alle Konfigs für den [Wiki Curator](https://wiki.avm.de/display/IT/Curator).

#### Schema

**[schemas](schemas/)** -> YAML-Artefakte zur Beschreibung des globalen Schemas.

#### Code

**[src](src/)** -> Code für Logstash-Tests und Schema-Generation


## Projekt Anpassungen

Wenn Anpassungen am Projekt vorgenommen werden müssen, kann das lokal vorbereitet und getestet werden.

### Setup

Einmalig müssen mittels `make setup` Abhängigkeiten für den [Kafka Consumer](run-kafka-consumer.sh) und die [Logstash Testumgebung](run-testbundle.sh) initialisiert werden.

### Pipeline anlegen

1. Pipeline mit Filter und Output im entsprechenden Verzeichnis anlegen
2. Pipeline in pipelines.yml definieren
3. Pipeline im entsprechenden Distributor Pattern aufnehmen
4. Pipeline testen (siehe nächster Abschnitt).
5. git Commit erstellen, nach gitlab pushen und mittels eine Merge-Requests in master-Branch mergen.
6. Nachdem der Merge-Request submitted wurde, läuft das [Deplyoment der Konfiguration ins Staging-System via Jenkins](https://jenkins.avm.de/job/elastic/job/logstash-config-sync-stage/).

### Pipeline testen

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

### Dokumentation aktualisieren

Nach dem Verändern von Pipelines sollte stets die Dokumentation (diese README.md) generiert und ins mit ins git eingecheckt werden werden. Die Generierung der README-Dokumentation geschieht mittels `./run-doc-generation.sh`

### Mapping-Template

Jedes Feld innerhalb aller zur Pipeline gehörigen Must-Dateien (JSON-Erwartungen) wird gemäß zugrunde liegender Schema-Definition automatisch in das Mapping übernommen, sofern auch eine Schema-Definition für dieses Feld vorliegt (d.h. sofern das Feld nicht verwaist ist). Alle benötigten Felder müssen also entweder Schema-treu benannt und durch Testfälle (MUST-Dateien) abgedeckt sein - oder alternativ manuell in das ensprechenden Mapping-Template (also die JSON-Datei neben dem Conf-File) eingetragen werden.

**Bei konfligierenden Schema-Definitionen gilt:**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; optionales &lt;pipeline>-template.json &nbsp;&nbsp;&nbsp; **überschreibt** &nbsp;&nbsp;&nbsp; yml-schemas &nbsp;&nbsp;&nbsp; **überschreibt** &nbsp;&nbsp;&nbsp; standard-template.json

##### Konsolenausgabe - inkl. Konsolen-Vorschau der Zuordnung aller erwarteten Felder (d.h. Felder aus MUST-Files) in die gegebene Schema-Definition:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Beispiel: `./run-show-template.sh pipelines/reporting-backend-service/fw-reports.conf`

##### Übertragung an Cluster http://172.16.78.100:9200

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Beispiel: `./run-submit-template.sh pipelines/reporting-backend-service/*.conf`

_Damit der Produktivbetrieb nicht gestört wird, werden die Templates während der Testphase nach dem Namensmuster genutil-prototest-&lt;beat_type>-&lt;service_type> angelegt._
_Auch die Index-Patterns werden während der Testphase nach dem Muster genutil-prototest-&lt;beat_type>-&lt;service_type> angelegt.*_
_Bei Erstellung eines pipeline-spezifischen Template-Skeletons <pipeline>-template.json im entsprechenden pipelines-Ordner kann jedoch schon Einfluss auf die Bezeichnung von Templates samt zugehöriger Indexe und Alias genommen werden - und zwar durch einen Eintrag der Form: `"index_patterns": [ "avm-nginx_access_log*" ]`_

Die Kommunikation läuft derzeit über http ohne Login-Daten. Kommunikation über https mit Login-Daten liegt im doc/genutil.py größtenteils bereits auskommentiert vor.

### Zusammenfassender Workflow zum Anlegen neuer Pipelines

1. Aktualität des ECS überprüfen `./doc/fieldscompare.sh`
2. ECS-Update mit Hilfe der Diff-Ausgabe aus Schritt 1 abwägen: `./doc/fieldsupdate.sh`
3. Ggf. neu benötigte Felder im Schema hinterlegen:
    * doc/ecs_extension.yml (für Erweiterungen am ECS-Schema)
    * doc/avm-schema/*.yml (hier liegen die Schema-Definitionen benutzerdefinierter AVM-Felder)
4. Input-Datei erstellen nach dem Muster: testing/pipelines/&lt;beat_type>/&lt;service_type>_[0-9]_in.json. Initial können die Daten gesammelt werden aus Kafka: `./run-kafka-consumer.sh --topic ("ops_filebeat" | "ops_metricbeat" | "ops_packetbeat") [--max-records number]`
5. Conf-Datei erstellen nach dem Muster: pipelines/&lt;beat_type>/&lt;service_type>.conf
6. Test ausführen, um den gewünschten initialen Input für die Must-Datei zu erhalten: `./run-testbundle.sh pipelines/<beat_type>/<service_type>.conf`
7. Must-Datei erstellen nach dem Muster: testing/pipelines/&lt;beat_type>/&lt;service_type>_[0-9]_must.json.
8. Mapping-Template überprüfen mit `./run-show-template.sh pipelines/<beat_type>/<service_type>.conf`
9. Feld-Doku neu generieren: `./run-doc-generator.sh`
10. (Experimentell) Mapping an Server übertragen: `./run-submit-template.sh pipelines/<beat_type>/<service_type>.conf`


### Curator Konfiguration

- Curator wird gegenwärtig stündlich per Cronjob gestartet
- Logs finden sich unter /var/log/curator/curator.log / Logrotate ist aktiviert
- entsprechende Action unter curator/actionfiles/ anlegen oder vorhandene editieren
- curator_cron.sh führt automatisch alle defininierten Actions aus

[Wiki Curator](https://wiki.avm.de/display/IT/Curator)

