import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = "bot.log"):
    """
    Настройка логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Имя файла для логов
    """
    # Создаем папку для логов, если ее нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file_path = log_dir / log_file
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка root логгера
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Настройка логгера для aiogram (уменьшаем уровень для избежания спама)
    aiogram_logger = logging.getLogger('aiogram')
    aiogram_logger.setLevel(logging.WARNING)
    
    # Настройка логгера для sqlalchemy
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с указанным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Объект логгера
    """
    return logging.getLogger(name)

# Дополнительные классы для логирования
class LoggingMiddleware:
    """Middleware для логирования запросов"""
    
    def __init__(self, logger):
        self.logger = logger
    
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        username = event.from_user.username if hasattr(event, 'from_user') else None
        
        self.logger.info(
            f"Received {event.__class__.__name__} "
            f"from user_id={user_id}, username={username}"
        )
        
        try:
            result = await handler(event, data)
            self.logger.info(
                f"Successfully processed {event.__class__.__name__} "
                f"for user_id={user_id}"
            )
            return result
        except Exception as e:
            self.logger.error(
                f"Error processing {event.__class__.__name__} "
                f"for user_id={user_id}: {str(e)}",
                exc_info=True
            )
            raise