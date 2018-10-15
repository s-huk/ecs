##Struktur

**input** -> Distributor Pattern (Filebeat,Metricbeat und Packetbeat)

**filebeat** -> Filebeat Filter + Output

**metricbeat** -> Metricbeat Filter + Output

**packetbeat** -> Packetbeat Filter + Output

**pipelines.yml** -> Definition aktiver Pipelines

##Pipeline anlegen

1. Pipeline mit Filter und Output im entsprechenden Verzeichnis anlegen
2. Pipeline in pipelines.yml definieren
3. Pipeline im entsprechenden Distributor Pattern aufnehmen
