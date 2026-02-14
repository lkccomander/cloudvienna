from backend.config import (
    API_HOST,
    API_PORT,
    API_PROXY_HEADERS,
    API_TLS_CERTFILE,
    API_TLS_KEYFILE,
)


def _ssl_kwargs() -> dict:
    certfile = API_TLS_CERTFILE
    keyfile = API_TLS_KEYFILE
    if certfile and keyfile:
        return {"ssl_certfile": certfile, "ssl_keyfile": keyfile}
    if certfile or keyfile:
        raise RuntimeError("Both API_TLS_CERTFILE and API_TLS_KEYFILE must be set together.")
    return {}


def main():
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        proxy_headers=API_PROXY_HEADERS,
        **_ssl_kwargs(),
    )


if __name__ == "__main__":
    main()
