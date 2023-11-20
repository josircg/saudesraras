from importlib import import_module

from django.db import models
from django.utils.translation import ugettext_lazy as _


class ActivationTask(models.Model):
    """Class to store tasks (functions) to execute after user activation"""
    email = models.EmailField(verbose_name=_('Task Email'))
    task_module = models.CharField(verbose_name=_('Task Module'), max_length=100)
    task_name = models.CharField(verbose_name=_('Task Name'), max_length=100)
    task_kwargs = models.JSONField(verbose_name=_('Task Parameters'))
    task_description = models.CharField(verbose_name=_('Task Description'), max_length=100)

    class Meta:
        unique_together = ('email', 'task_module', 'task_name', 'task_kwargs')

    def __str__(self):
        return f'{self.email} - {self.task_description}'

    def execute_task(self, **kwargs):
        module = import_module(self.task_module)

        func = getattr(module, self.task_name)

        params = {}
        params.update(self.task_kwargs)
        params.update(kwargs)

        return func(**params)
