"""Unsubscribe handlers for various methods."""

from gmail_unsub.unsubscribe.browser import BrowserHandler
from gmail_unsub.unsubscribe.handler import UnsubscribeHandler
from gmail_unsub.unsubscribe.mailto_handler import MailtoHandler
from gmail_unsub.unsubscribe.one_click import OneClickHandler

__all__ = [
    "UnsubscribeHandler",
    "OneClickHandler",
    "MailtoHandler",
    "BrowserHandler",
]
