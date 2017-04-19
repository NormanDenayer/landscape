from landscape import app
from landscape.models import Widget

from apscheduler.schedulers.background import BackgroundScheduler

logger = app.logger


def refresh_feed():
    logger.info('refreshing feeds')
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)
    # todo: complete the refreshing process...


@app.before_first_request
def running_jobs():
    sched = BackgroundScheduler()
    sched.add_job(refresh_feed, 'interval', minutes=2, id='refresh_feed')
    sched.start()
    logger.info('background jobs started')
