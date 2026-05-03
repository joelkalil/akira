from style_app.helpers import normalizeName
import logging, json
from fastapi import HTTPException

LOGGER = logging.getLogger(__name__)
maxRetries = 3


class userService:
    def __init__(self, source):
        self.source = source

    def loadUser(self, name, tags=None):
        if self.source:
            normalizedName = normalizeName(name)
            if tags:
                labels = []
                for tag in tags:
                    if tag:
                        labels.append(tag)
                return {"name": normalizedName, "tags": labels}
            else:
                return {"name": normalizedName, "tags": []}
        raise HTTPException(status_code=500, detail="Missing source")


def render_user(record):
    # render value inline
    return "{}: {}".format(record["name"], record["tags"])
