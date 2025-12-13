import logging
import time


class UTCFormatter(logging.Formatter):
    converter = time.gmtime

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%dT%H:%M:%SZ", ct)
        return t


def setup_format():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname).3s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    for handler in logging.getLogger().handlers:
        handler.setFormatter(UTCFormatter(
            "%(asctime)s %(levelname).3s %(message)s", "%Y-%m-%dT%H:%M:%SZ"))
