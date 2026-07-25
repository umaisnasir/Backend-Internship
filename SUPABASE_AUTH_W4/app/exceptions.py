from __future__ import annotations


class ApiError(Exception):
    """
    Application-level exception converted into a JSON API response.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.headers = headers
        super().__init__(message)