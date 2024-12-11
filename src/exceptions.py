from fastapi.exceptions import HTTPException


class BadRequestError(HTTPException):  # pragma: no cover
    def __init__(self, detail):
        super().__init__(detail=f"BadRequest: {detail}", status_code=400)


class UnauthorizedError(HTTPException):  # pragma: no cover
    def __init__(self, detail):
        super().__init__(detail=f"Unauthorized: {detail}", status_code=401)


class ForbiddenError(HTTPException):  # pragma: no cover
    def __init__(self, detail):
        super().__init__(detail=f"Forbidden: {detail}", status_code=403)


class NotFoundError(HTTPException):  # pragma: no cover
    def __init__(self, detail):
        super().__init__(detail=f"NotFound: {detail}", status_code=404)


class InternalError(HTTPException):  # pragma: no cover
    def __init__(self, detail):
        super().__init__(detail=f"Internal Error: {detail}", status_code=500)
