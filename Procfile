web: gunicorn p2p_exchange.wsgi --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput