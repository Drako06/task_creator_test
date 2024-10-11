from django.db import models

# Create your models here.


class Task(models.Model):
    title = models.CharField(max_length=50, null=False)
    email = models.EmailField(max_length=50, null=False)
    description = models.CharField(blank=True, null=False)
