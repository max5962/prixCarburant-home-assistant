[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
# prixCarburant-home-assistant
Client python permettant d'interroger l'openData du gouvernement sur le prix du carburant.

https://www.prix-carburants.gouv.fr/

Le client permet de :
 - Trouver les stations les plus proches dans un cercle de X km configurable a partir de votre adresse defini dans home assistant
 - Extraire des stations spécifiques via son ID


Aide à l'installation depuis HACS :

Dans HACS, cliquer sur ... puis depots personnalisés

Ajouter :

- URL : https://github.com/ryann72/prixCarburant-home-assistant
- Catégorie : Intégration

## Configuration
Exemple de configuration :
A ajouter dans la partie sensor ou sous la partie sensor de votre confirguration.yaml rn fonction du découpage de votre configuration.

### Configuration pour récupérer les stations dans un rayon de 20 km
```
sensor:
  platform: prixCarburant
  maxDistance: 20
```

### Configuration pour récupérer les stations très spécifique

Deux options pour connaitres les identifiants : 

1 - Faire une recherche dans un cercle de 10 km par exemple

Puis récupérer dans les outils de développement →  etats →  les sensors commençants par PrixCarburant_ (la valeur après le _ est l'id). 

2 - Télécharger le fichier des prix disponnible ici : https://donnees.roulez-eco.fr/opendata/instantane 

Puis rechercher dedans les "id" des stations qui vous intéressent (ex :  <pdv id="26290008" latitude="4443600" longitude="471700" cp="26290" pop="R">) 



```
sensor:
  platform: prixCarburant
  stationID:
    - 59000009
    - 59000080
```


Exemple de données extraites :
```
Station ID: '44300020'
Gasoil: '1.519'
Last Update Gasoil: '2021-02-23T19:23:06'
E95: '1.622'
Last Update E95: '2021-02-23T19:23:07'
E98: '1.685'
Last Update E98: '2021-02-23T19:23:08'
E10: '1.563'
Last Update E10: '2021-02-23T19:23:07'
E85: None
Last Update E85: ''
GPLc: '0.909'
Last Update GPLc: '2021-02-23T19:23:07'
Station Address: 162 Route de Rennes Nantes
Station name: undefined
Last update: '2021-02-24'
unit_of_measurement: €
friendly_name: PrixCarburant_44300020
icon: 'mdi:currency-eur'
```
### Configuration d'affichage dans Home Assistant

#### via carte markdown statique

Permet d'afficher le prix des différents carburants proposés par la station.

La date d'actualisation des prix est également affichée

Ajouter une carte type 'Manuel' puis coller le code suivant : 
```
{{state_attr("sensor.prixcarburant_44300020", "Station name")}} - Maj : {{state_attr("sensor.prixcarburant_44300020", "Last update")}}
{%- if state_attr("sensor.prixcarburant_44300020", "Gasoil") != "None"  %}
Gasoil : {{ state_attr("sensor.prixcarburant_44300020", "Gasoil") }} €
{%- endif %}
{%- if state_attr("sensor.prixcarburant_44300020", "E10") != "None"  %}
E10 : {{ state_attr("sensor.prixcarburant_44300020", "E10") }} €
{%- endif %}
{%- if state_attr("sensor.prixcarburant_44300020", "E95") != "None"  %}
SP95 : {{ state_attr("sensor.prixcarburant_44300020", "E95") }} €
{%- endif %}
{%- if   state_attr("sensor.prixcarburant_44300020", "E98") != "None"  %}
SP98 : {{ state_attr("sensor.prixcarburant_44300020", "E98") }} €
{%- endif %}
{%- if   state_attr("sensor.prixcarburant_44300020", "GPLc") != "None"  %}
GPLc : {{ state_attr("sensor.prixcarburant_44300020", "GPLc") }} €
{%- endif %}
```

#### via carte markdown dynamique

![alt text](https://forum.hacf.fr/uploads/default/original/2X/6/68418b4f3fcc38b584ce3f56efe0121c251f5d6b.png)

Le but est d'avoir un groupe de station essence et de trié automatiquement la liste sur le prix.

* Crée un groupe avec les stations essences désirer

Pour creer le groupe, il faut passer ajouter ceci dans votre configuration.yaml

```
group:
  station_essence:
  - sensor.prixcarburant_38220002
  - sensor.prixcarburant_38320006
  - sensor.prixcarburant_38800003
  - sensor.prixcarburant_38700003
```

Si votre configuration est découpée, il doit y avoir un fichier groups.yaml et vous devez ajouter seulement le code suivant. 

```
  station_essence:
  - sensor.prixcarburant_38220002
  - sensor.prixcarburant_38320006
  - sensor.prixcarburant_38800003
  - sensor.prixcarburant_38700003
```

* Carte markdown dynamique

Ajouter une carte type 'Manuel' puis coller le code suivant :


```
type: markdown
content: >-
  {% set update = states('sensor.date') %}

  {% set midnight = now().replace(hour=0, minute=0, second=0,
  microsecond=0).timestamp() %}

  {% set sorted_station_essence = "group.station_essence" | expand |
  sort(attribute='attributes.Gasoil') %}
    | Station | &nbsp;&nbsp;&nbsp;&nbsp;Gasoil&nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp;Gpl&nbsp;&nbsp;&nbsp;&nbsp; | Update |
    | :------- | :----: | :----: | ------: |
  {% for station in sorted_station_essence %}| {{-
  state_attr(station.entity_id, 'Station name') -}}
    |{%- if state_attr(station.entity_id, "Gasoil") == "None" -%}-{%- else -%}{{- state_attr(station.entity_id, 'Gasoil') -}}{%- endif -%}
    |{%- if state_attr(station.entity_id, "GPLc") == "None" -%}-{%- else -%}{{- state_attr(station.entity_id, 'GPLc') -}}{%- endif -%}
  {%- set event = state_attr(station.entity_id,'Last Update Gasoil') |
  as_timestamp -%}
  {%- set delta = ((event - midnight) // 86400) | int -%}
    |{{ -delta }} Jours|
  {% endfor %}
title: Prix des carburants
```

#### via carte multiple-entity-row

Celle-ci nécéssite une integration supplémentaire : https://github.com/benct/lovelace-multiple-entity-row

![alt text](https://forum.hacf.fr/uploads/default/original/2X/5/5bcb6d091aa764431ddb271c3087c7544013c599.png)

```
type: entities
title: Prix carburants
entities:
  - entity: sensor.prixcarburant_12340001
    type: custom:multiple-entity-row
    name: Auchan
    icon: mdi:gas-station
    show_state: false
    entities:
      - attribute: E98
        name: E98
        unit: €
      - attribute: E10
        name: E10
        unit: €
      - attribute: GPLc
        name: GPL
        unit: €
  - entity: sensor.prixcarburant_12340003
    type: custom:multiple-entity-row
    name: E.Leclerc
    icon: mdi:gas-station
    show_state: false
    entities:
```

# Information

Source code du client si vous souhaitez contribuer : "https://github.com/ryann72/essence"

Il s'agit d'un fork de https://github.com/max5962/prixCarburant-home-assistant, mis à jour afin de recuperer le E85 et le GPLc
