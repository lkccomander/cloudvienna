from backend.config import (
    APP_ENV,
    API_HOST,
    API_PORT,
    API_PROXY_HEADERS,
    API_TLS_CERTFILE,
    API_TLS_KEYFILE,
    DB_HOST,
    DB_NAME,
    DB_PORT,
    ENV_FILES_PRESENT,
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

    env_sources = ", ".join(ENV_FILES_PRESENT) if ENV_FILES_PRESENT else "none"
    print(
        f"[backend] startup env={APP_ENV} db={DB_NAME}@{DB_HOST}:{DB_PORT} "
        f"env_files={env_sources}"
    )

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        proxy_headers=API_PROXY_HEADERS,
        **_ssl_kwargs(),
    )


if __name__ == "__main__":
    main()
