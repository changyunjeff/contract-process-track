from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, message: str = "Not Found"):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.message = message
        super().__init__(status.HTTP_404_NOT_FOUND)

class BadRequestException(HTTPException):
    def __init__(self, message: str = "Bad Request"):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.message = message
        super().__init__(status.HTTP_400_BAD_REQUEST)

class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "Unauthorized"):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.message = message
        super().__init__(status.HTTP_401_UNAUTHORIZED)

class ForbiddenException(HTTPException):
    def __init__(self, message: str = "Forbidden"):
        self.status_code = status.HTTP_403_FORBIDDEN
        self.message = message
        super().__init__(status.HTTP_403_FORBIDDEN)