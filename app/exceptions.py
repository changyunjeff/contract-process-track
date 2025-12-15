from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, message: str = "Not Found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )


class BadRequestException(HTTPException):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )


class ForbiddenException(HTTPException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )


class ServerUnavailableException(HTTPException):
    def __init__(self, message: str = "Server Unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )


class InternalServerException(HTTPException):
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )
