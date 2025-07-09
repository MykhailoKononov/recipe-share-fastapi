import os

import config
from config import Config

from fastapi_mail import FastMail, ConnectionConfig


TEMPLATE_FOLDER = os.path.join(config.BASE_DIR, 'templates', 'mail')

mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    MAIL_STARTTLS=Config.MAIL_STARTTLS,
    MAIL_SSL_TLS=Config.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
)

fm = FastMail(
    config=mail_config
)
