from django.utils import timezone
from django.db import models


class Job(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Person(models.Model):
    job = models.ForeignKey(Job, null=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    date_of_birth = models.DateField()

    @property
    def age(self):
        return (timezone.now().date() - self.date_of_birth).days

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
