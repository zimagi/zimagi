from django.conf.urls import include, url

from systems.api import routers


urlpatterns = [
    url(r'^', include(routers.CommandAPIRouter().urls))
]
