from celery import Celery


def make_celery(app):
    celery_obj = Celery(app.import_name)
    celery_obj.conf.update(app.config['CELERY_CONFIG'])

    class ContextTask(celery_obj.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_obj.Task = ContextTask
    return celery_obj
