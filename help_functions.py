import functools
import time
import logging

def log_method(func):
    """Декоратор: логирует вход, выход и ошибки при вызове метода."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.time()
        logging.info(f"▶️  Вызов: {func.__name__}()")
        try:
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start
            logging.info(f"✅ Завершено: {func.__name__}() — {elapsed:.2f} сек")
            return result
        except Exception as e:
            logging.error(f"❌ Ошибка в {func.__name__}(): {e}")
            raise
    return wrapper