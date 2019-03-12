# prixCarburant-home-assistant
Client python permettant d'interroger l'openData du gouvernement sur le prix du carburant.
Le client permet de :
 - Trouver les stations les plus proches dans un cercle de X km comfigurable
 - Extraire des stations spécifiques via son ID
 
 
Exemple de configuration:

### Configuration pour récupérer les stations dans un rayon de 20 km
```
sensor:
  platform: prixCarburant
  maxDistance: 20
```

### Configuration pour récupérer les stations très spécifique   
```
sensor:
  platform: prixCarburant
  #maxDistance: 20
  stationID:
    - 59000009
    - 59000080
```
