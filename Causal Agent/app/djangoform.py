from django.db import models
from django_jsonform.models.fields import JSONField


class ShoppingList(models.Model):
    ITEMS_SCHEMA = {
        'type': 'array', # a list which will contain the items
        'items': {
            'type': 'string' # items in the array are strings
        }
    }

    items = JSONField(schema=ITEMS_SCHEMA)
    date_created = models.DateTimeField(auto_now_add=True)

