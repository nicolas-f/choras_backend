from celery import Celery


def make_celery(app):
    celery_app = Celery(app.import_name)
    celery_app.conf.update(app.config['CELERY_CONFIG'])
    celery_app.conf.broker_connection_retry_on_startup = True

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
