import platform

from fastapi import APIRouter, Request
import platform




router = APIRouter()

@router.get("/", summary="API Root", tags=["General"], responses={
    200: {
        "description": "API information.",
        "content": {
            "application/json": {
                "example": {
                    "name": "FreeDATA API",
                    "description": "A sample API that provides free data services",
                    "api_version": 3,
                    "modem_version": "0.16.8-alpha",
                    "license": "GPL3.0",
                    "documentation": "https://wiki.freedata.app"
                }
            }
        }
    },
    404: {
        "description": "The requested resource was not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found."
                }
            }
        }
    },
    503: {
        "description": "Service unavailable.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Service unavailable."
                }
            }
        }
    }
})
async def index(request: Request):
    """
    Retrieve API metadata.

    Returns:
        dict: A JSON object containing API metadata.
    """
    return {
        'name': 'FreeDATA API',
        'description': 'A sample API that provides free data services',
        'api_version': request.app.API_VERSION,
        'modem_version': request.app.MODEM_VERSION,
        'license': "GPL3.0",
        'documentation': "https://wiki.freedata.app",
    }

@router.get("/version", summary="Get Modem Version", tags=["General"], responses={
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "api_version": 3,
                    "modem_version": "0.16.8-alpha",
                    "os_info": {
                        "system": "Linux",
                        "node": "my-node",
                        "release": "5.4.0-74-generic",
                        "version": "#83-Ubuntu SMP Mon May 10 16:30:51 UTC 2021",
                        "machine": "x86_64",
                        "processor": "x86_64"
                    },
                    "python_info": {
                        "build": ["default", "May  3 2021 19:12:05"],
                        "compiler": "GCC 9.3.0",
                        "branch": "",
                        "implementation": "CPython",
                        "revision": "",
                        "version": "3.8.5"
                    }
                }
            }
        }
    }
})
async def get_modem_version(request: Request):
    """
    Retrieve the modem version, API version, OS information, and Python information.

    Returns:
        dict: A JSON object containing version information.
    """
    os_info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
    }

    python_info = {
        'build': platform.python_build(),
        'compiler': platform.python_compiler(),
        'branch': platform.python_branch(),
        'implementation': platform.python_implementation(),
        'revision': platform.python_revision(),
        'version': platform.python_version()
    }

    return {
        'api_version': request.app.API_VERSION,
        'modem_version': request.app.MODEM_VERSION,
        'os_info': os_info,
        'python_info': python_info
    }
