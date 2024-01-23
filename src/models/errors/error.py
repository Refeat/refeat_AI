import functools
import threading
import ctypes
import signal
class ChainRunError(Exception):
    """Chain 실행 중 발생하는 에러를 나타내는 커스텀 예외 클래스"""

    def __init__(self, message="Failed to run chain", class_name=None, errors=None):
        super().__init__(message)
        self.class_name = class_name
        self.errors = errors

    def __str__(self):
        class_info = f"{self.class_name}: " if self.class_name else ""
        return f"{class_info}{self.args[0]}"
    
class WebLoaderError(Exception):
    """WebLoader 실행 중 발생하는 에러를 나타내는 예외 클래스"""

    def __init__(self, message="Failed to run WebLoader", errors=None):
        super().__init__(message)
        self.errors = errors

    def __str__(self):
        return f"{self.args[0]}"
    
class ChainTimeoutError(TimeoutError):
    """특정 Chain 실행 중 시간 초과로 발생하는 커스텀 예외 클래스"""

    def __init__(self, message=""):
        super().__init__(message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]}"

def timeout_handler(signum, frame):
    raise ChainTimeoutError("Operation took more than the allowed time")

# pthread_kill 함수를 가져옴
libc = ctypes.CDLL('libc.so.6')
pthread_kill = libc.pthread_kill
pthread_kill.argtypes = [ctypes.c_void_p, ctypes.c_int]

def terminate_thread(thread):
    if not thread.is_alive():
        return

    res = pthread_kill(ctypes.c_void_p(thread.ident), signal.SIGTERM)
    if res != 0:
        raise ValueError("스레드 종료 실패")

def timeout(timeout_duration):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout_duration))]
            
            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = threading.Thread(target=newFunc)
            t.daemon = True
            t.start()
            t.join(timeout_duration)

            if t.is_alive():
                terminate_thread(t)  # 스레드 강제 종료
                t.join()

            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret
        return wrapper
    return decorator