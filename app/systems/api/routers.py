from django.conf.urls import url

from rest_framework.routers import BaseRouter, Route, DynamicRoute


class CommandAPIRouter(BaseRouter):

    def get_urls(self):
        urls = []
        return urls
