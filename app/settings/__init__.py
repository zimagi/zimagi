try:
    import celery  # noqa: F401

    add_celery_service = True

except Exception:
    add_celery_service = False

if add_celery_service:
    from services.celery import app as celery_app

    __all__ = ["celery_app"]
