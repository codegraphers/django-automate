from django.urls import include, path

urlpatterns = [
    path("v1/", include("automate_api.v1.urls")),
]
