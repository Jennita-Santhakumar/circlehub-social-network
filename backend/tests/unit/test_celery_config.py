from config.celery import app


def test_beat_schedule_has_prune_task():
    schedule = app.conf.beat_schedule
    assert "prune-old-read-notifications" in schedule
    entry = schedule["prune-old-read-notifications"]
    assert entry["task"] == "social.tasks.prune_old_notifications"
    assert entry["kwargs"] == {"days": 30}


def test_celery_app_name():
    assert app.main == "socialpulse"
