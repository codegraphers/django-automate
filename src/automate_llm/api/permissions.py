from rest_framework.permissions import BasePermission


class DjangoPerm(BasePermission):
    perm: str = ""

    def has_permission(self, request, view) -> bool:
        if not self.perm:
            return True
        return bool(request.user and request.user.has_perm(self.perm))


class CanViewRuns(DjangoPerm):
    perm = "automate_llm.view_llmrun"


class CanRunRuns(DjangoPerm):
    perm = "automate_llm.run_llmrun"


class CanManagePrompts(DjangoPerm):
    perm = "automate_llm.change_prompt"
