from django.db import models

from ..workflows.models import Automation


class RuleSpec(models.Model):
    automation = models.ForeignKey(Automation, related_name="rules", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    conditions = models.JSONField(default=dict)  # JsonLogic
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Rule {self.id} for {self.automation.slug}"
