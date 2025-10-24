from django.db import models

# Create your models here.
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField()
    tax = models.FloatField()

    def __str__(self):
        return self.name