# -*- coding: utf-8 -*-
import logging

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def get_price(article, user):
    return "%.02f" % article.get_price(user)
