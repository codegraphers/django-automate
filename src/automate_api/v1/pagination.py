from rest_framework.pagination import CursorPagination as DRFCursorPagination


class CursorPagination(DRFCursorPagination):
    page_size = 50
    ordering = "-created_at" # Default

    def get_ordering(self, request, queryset, view=None):
        if hasattr(view, "ordering"):
             return view.ordering
        return super().get_ordering(request, queryset, view)
