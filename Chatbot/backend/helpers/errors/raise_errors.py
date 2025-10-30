from fastapi import HTTPException, status


def raise_http_error(
    status_code: int = status.HTTP_400_BAD_REQUEST, detail: str = "An error occurred"
):
    """
    Utility function to raise a standardized HTTPException.
    """
    raise HTTPException(status_code=status_code, detail=detail)
