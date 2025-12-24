from django.shortcuts import render, redirect
from django.contrib import admin, messages
from django.urls import path
from django.utils.html import format_html
from ..models import Automation, TriggerSpec, Workflow

class AutomationWizardView:
    """
    A step-by-step wizard for creating Automations.
    Track C requirement.
    """
    def as_view(self, request):
        if request.method == "POST":
            return self.post(request)
        return self.get(request)

    def get(self, request):
        ctx = admin.site.each_context(request)
        ctx["title"] = "Create Automation Wizard"
        return render(request, "admin/automate/automation/wizard.html", ctx)

    def post(self, request):
        step = request.POST.get("step")
        
        if step == "create":
            name = request.POST.get("name")
            slug = request.POST.get("slug")
            trigger_type = request.POST.get("trigger_type")
            
            # 1. Create Automation
            auto = Automation.objects.create(name=name, slug=slug)
            
            # 2. Create Trigger
            TriggerSpec.objects.create(
                automation=auto,
                type=trigger_type,
                config={} # Empty config for now, would be wizard step 2
            )
            
            # 3. Create Draft Workflow
            Workflow.objects.create(
                automation=auto,
                version=1,
                graph={"nodes": [], "edges": []}
            )
            
            messages.success(request, f"Automation '{name}' created!")
            return redirect(f"/admin/automate/automation/{auto.id}/change/")
            
        return redirect("/admin/automate/automation/")
