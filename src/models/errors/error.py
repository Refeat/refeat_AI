class ChainRunError(Exception):
    """Chain 실행 중 발생하는 에러를 나타내는 커스텀 예외 클래스"""

    def __init__(self, message="Failed to run chain", class_name=None, errors=None):
        super().__init__(message)
        self.class_name = class_name
        self.errors = errors

    def __str__(self):
        class_info = f"{self.class_name}: " if self.class_name else ""
        return f"{class_info}{self.args[0]}"
    
class WebLoadException(Exception):
    def __str__(self) -> str:
        print("WebLoadException")
        return super().__str__()
    
class PdfLoadException(Exception):
    def __str__(self) -> str:
        print("PdfLoadException")
        return super().__str__()
class AIFailException(Exception):
    def __str__(self) -> str:
        print("AIFailException")
        return super().__str__()