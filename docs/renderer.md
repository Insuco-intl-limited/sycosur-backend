# GenericJSONRenderer

## Description

`GenericJSONRenderer` est une classe de rendu JSON personnalisée pour Django REST Framework qui standardise le format des réponses API. Cette classe hérite de `JSONRenderer` de DRF et encapsule les données de réponse dans une structure cohérente pour maintenir une API uniforme.

## Format de réponse

La classe standardise toutes les réponses API réussies dans le format suivant :

```json
{
    "status_code": 200,
    "object_label": { /* données de réponse */ }
}
```

Où :
- `status_code` est le code HTTP de la réponse (200, 201, etc.)
- `object_label` est une clé dynamique qui peut être personnalisée par vue

## Installation et configuration

### Dans settings.py

Pour utiliser ce renderer globalement dans votre projet Django :

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'core_apps.common.renderers.GenericJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # autres configurations DRF...
}
```

### Pour une vue spécifique

Vous pouvez également l'appliquer à une vue spécifique :

```python
from rest_framework.views import APIView
from core_apps.common.renderers import GenericJSONRenderer

class MaVueAPI(APIView):
    renderer_classes = [GenericJSONRenderer]
    # reste de la vue...
```

## Personnalisation par vue

Vous pouvez personnaliser l'étiquette d'objet (object_label) pour chaque vue en définissant l'attribut `object_label` :

```python
class UtilisateursListView(ListAPIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = "utilisateurs"
    # Le reste de votre vue...
```

Cela produirait une réponse au format :

```json
{
    "status_code": 200,
    "utilisateurs": [ /* liste d'utilisateurs */ ]
}
```

## Gestion des erreurs

Le renderer préserve le format d'erreur standard de Django REST Framework. Si la réponse contient une clé "errors", le renderer transmettra les données directement au renderer parent sans modifier la structure.

## Exemple d'utilisation complet

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from core_apps.common.renderers import GenericJSONRenderer

class ProfileView(APIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = "profile"

    def get(self, request, *args, **kwargs):
        # Logique pour récupérer le profil...
        profile_data = {"id": 1, "name": "Utilisateur", "email": "user@example.com"}
        return Response(profile_data)
```

Cette vue produirait une réponse au format :

```json
{
    "status_code": 200,
    "profile": {
        "id": 1, 
        "name": "Utilisateur", 
        "email": "user@example.com"
    }
}
```

## Considérations techniques

- Le renderer utilise l'encodage UTF-8 par défaut
- Il extrait automatiquement le code d'état de l'objet de réponse
- Il lève une exception `ValueError` si l'objet de réponse est absent du contexte
