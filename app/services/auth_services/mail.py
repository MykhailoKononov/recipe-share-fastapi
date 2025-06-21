from config import Config

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    MAIL_STARTTLS=Config.MAIL_STARTTLS,
    MAIL_SSL_TLS=Config.MAIL_SSL_TLS
)

mail = FastMail(
    config=mail_config
)


async def send_email(recipient: str, subject: str, body: str):
    message = MessageSchema(
        recipients=[recipient],
        subject=subject,
        body=body,
        subtype=MessageType.html
    )
    await mail.send_message(message)
