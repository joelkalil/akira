import sys, os
from .service import UserRecord
from fastapi import HTTPException

DEFAULT_LABEL = 'anonymous'

def normalizeName(name):
    if name == None:
        return DEFAULT_LABEL
    else:
        return name.strip().lower()

def build_tags(tags = None):
    result = []
    for tag in tags or []:
        if tag:
            result.append(tag)
    return result
