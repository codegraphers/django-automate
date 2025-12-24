from django.urls import path
from .views.wizard import AutomationWizardView
from .views.tester import RuleTesterView
from .views.explorer import ExecutionExplorerView

urlpatterns = [
    path('wizard/', AutomationWizardView.as_view(), name='studio_wizard'),
    path('tester/', RuleTesterView.as_view(), name='studio_tester'),
    path('explorer/<str:run_id>/', ExecutionExplorerView.as_view(), name='studio_explorer_detail'),
]
