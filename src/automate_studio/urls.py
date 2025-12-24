from django.urls import path

from .views.explorer import ExecutionExplorerView
from .views.tester import RuleTesterView
from .views.wizard import AutomationWizardView

urlpatterns = [
    path('wizard/', AutomationWizardView.as_view(), name='studio_wizard'),
    path('tester/', RuleTesterView.as_view(), name='studio_tester'),
    path('explorer/<str:run_id>/', ExecutionExplorerView.as_view(), name='studio_explorer_detail'),
]
