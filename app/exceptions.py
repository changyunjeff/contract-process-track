from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, message: str = "Not Found"):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.message = message
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)

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

class ServerUnavailableException(HTTPException):
    def __init__(self, message: str = "Server Unavailable"):
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        self.detail = message
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE)

class InternalServerException(HTTPException):
    def __init__(self, message: str = "Internal Server Error"):
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.detail = message
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR)
