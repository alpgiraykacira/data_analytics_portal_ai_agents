import logging
import logging.handlers
import os
import time
import sys

class OptimizedLogger:
    """
    Optimized logger with performance improvements and better resource management
    """
    _loggers = {}  # Class-level cache for logger instances
    
    @classmethod
    def get_logger(cls, name: str = '', log_file: str = 'agent.log', level: str = 'INFO'):
        """
        Get or create a cached logger instance
        
        Args:
            name: Logger name (defaults to calling module)
            log_file: Log file path
            level: Logging level as string
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Use calling module name if not provided
        if name is None:
            frame = sys._getframe(1)
            name = frame.f_globals.get('__name__', 'unknown')
            
        # Create cache key
        cache_key = f"{name}:{log_file}:{level}"
        
        # Return cached logger if exists
        if cache_key in cls._loggers:
            return cls._loggers[cache_key]
            
        # Create new logger
        logger = cls._create_logger(name, log_file, level)
        cls._loggers[cache_key] = logger
        
        return logger
    
    @classmethod
    def _create_logger(cls, name: str, log_file: str, level: str) -> logging.Logger:
        """Create and configure a new logger"""
        logger = logging.getLogger(name)
        
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Prevent duplicate handlers
        if logger.hasHandlers():
            return logger
            
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # Use RotatingFileHandler to prevent large log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB max file size
            backupCount=5,  # Keep 5 backup files
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler with higher threshold for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Optimized formatter - less verbose in production
        if numeric_level <= logging.DEBUG:
            # Detailed format for debug
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            # Simpler format for production
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        return logger

# Backward compatibility function
def setup_logger(log_file: str = 'agent.log', level: str = 'INFO') -> logging.Logger:
    """
    Backward compatible setup function
    
    Args:
        log_file: Path to log file
        level: Logging level as string
        
    Returns:
        logging.Logger: Configured logger
    """
    # Get caller's module name for logger naming
    frame = sys._getframe(1)
    caller_name = frame.f_globals.get('__name__', 'agent')
    
    return OptimizedLogger.get_logger(caller_name, log_file, level)

# Environment-based configuration
def get_log_level():
    """Get log level from environment or default to INFO"""
    env_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    return env_level if env_level in valid_levels else 'INFO'

# Context manager for temporary log level changes
class LogLevelContext:
    """Context manager to temporarily change log level"""
    
    def __init__(self, logger, temp_level):
        self.logger = logger
        self.temp_level = getattr(logging, temp_level.upper())
        self.original_level = logger.level
        
    def __enter__(self):
        self.logger.setLevel(self.temp_level)
        return self.logger
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)

# Performance monitoring decorator
def log_performance(func):
    """Decorator to log function execution time"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = OptimizedLogger.get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Only log slow operations
                logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
                
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
            
    return wrapper

# Batch logging for high-frequency operations
class BatchLogger:
    """Logger that batches messages to reduce I/O operations"""
    
    def __init__(self, logger, batch_size=10, flush_interval=5.0):
        self.logger = logger
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.messages = []
        self.last_flush = time.time()
        
    def log(self, level, message):
        """Add message to batch"""
        import time
        
        self.messages.append((level, message, time.time()))
        
        # Flush if batch is full or interval exceeded
        if (len(self.messages) >= self.batch_size or 
            time.time() - self.last_flush > self.flush_interval):
            self.flush()
    
    def flush(self):
        """Flush all batched messages"""
        if not self.messages:
            return
            
        for level, message, timestamp in self.messages:
            getattr(self.logger, level.lower())(message)
            
        self.messages.clear()
        self.last_flush = time.time()
    
    def __del__(self):
        """Ensure messages are flushed on destruction"""
        self.flush()

# Example usage and migration guide
if __name__ == "__main__":
    # Basic usage (drop-in replacement)
    logger = setup_logger()
    logger.info("This works exactly like before")
    
    # Advanced usage with specific configuration
    api_logger = OptimizedLogger.get_logger("api_agent", "logs/api.log", "DEBUG")
    api_logger.debug("Detailed API logging")
    
    # Temporary log level change
    with LogLevelContext(logger, "DEBUG") as debug_logger:
        debug_logger.debug("This will be logged even if logger was at INFO level")
    
    # Performance monitoring
    @log_performance
    def slow_function():
        import time
        time.sleep(2)
        return "done"
    
    slow_function()  # Will automatically log execution time
    
    # Batch logging for high-frequency operations
    batch_logger = BatchLogger(logger)
    for i in range(20):
        batch_logger.log("INFO", f"High frequency message {i}")
    batch_logger.flush()  # Manual flush