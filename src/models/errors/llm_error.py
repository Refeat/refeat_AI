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
    
class ChainTimeoutError(TimeoutError):
    """특정 Chain 실행 중 시간 초과로 발생하는 커스텀 예외 클래스"""

    def __init__(self, message=""):
        super().__init__(message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]}"

def timeout_handler(signum, frame):
    raise ChainTimeoutError("Operation took more than the allowed time")

def run_chain_with_timeout(chain, input_dict, callbacks, timeout_duration):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_duration)

    try:
        result = chain.run(input_dict, callbacks=callbacks)
        signal.alarm(0)  # 타이머 해제
        return result
    except ChainTimeoutError as e:
        print(e)
        # 추가적인 정리 작업이 필요한 경우 여기서 수행
        raise