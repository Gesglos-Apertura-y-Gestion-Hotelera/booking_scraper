import logging
import os
from datetime import datetime
from pathlib import Path
import inspect

# Crear directorio logs si no existe
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')


class PyCharmCallerFormatter(logging.Formatter):
    def format(self, record):
        # Usar formato nativo de logging (funciona automáticamente)
        record.caller_file = "%(pathname)s:%(lineno)d" % record.__dict__

        # Stack para caller REAL (salta logger internals)
        try:
            stack = inspect.stack()
            # 0: este método, 1: handler, 2: logger.info, 3: caller real
            caller_frame = stack[3]
            real_file = Path(caller_frame.filename).name
            real_line = caller_frame.lineno
            record.real_caller = f"{real_file}:{real_line}"
        except:
            record.real_caller = "unknown"

        return super().format(record)


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formatter mejorado
    formatter = PyCharmCallerFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | '
        '🔗 [%(pathname)s:%(lineno)d]'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler con colores
    import sys
    class ColoredFormatter(PyCharmCallerFormatter):
        LEVEL_COLORS = {
            'INFO': '\x1b[32m',  # Verde
            'WARNING': '\x1b[33m',  # Amarillo
            'ERROR': '\x1b[31m',  # Rojo
            'CRITICAL': '\x1b[35m'  # Magenta
        }

        def format(self, record):
            msg = super().format(record)
            color = self.LEVEL_COLORS.get(record.levelname, '')
            return f"{color}{msg}\x1b[0m"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(formatter._fmt))
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
