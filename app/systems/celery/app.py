from celery import Celery as BaseCelery


class Celery(BaseCelery):
    registry_cls = "systems.celery.registry:CommandTaskRegistry"
