from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from live_info.models import Event, User
from live_info.notifiers.renderer import render_email

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int
    user: str | None
    password: str | None
    sender: str


class EmailNotifier:
    def __init__(self, cfg: SMTPConfig):
        self.cfg = cfg

    def send(self, user: User, events: list[Event]) -> bool:
        if not user.email or not events:
            return False
        subject, html = render_email(events)
        msg = EmailMessage()
        msg["From"] = self.cfg.sender
        msg["To"] = user.email
        msg["Subject"] = subject
        msg.set_content("请使用支持 HTML 的客户端查看本邮件。")
        msg.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(self.cfg.host, self.cfg.port) as smtp:
                smtp.starttls()
                if self.cfg.user and self.cfg.password:
                    smtp.login(self.cfg.user, self.cfg.password)
                smtp.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError) as e:
            log.warning("email %s error: %s", user.name, e)
            return False
