from fastapi import HTTPException
from fastapi.responses import JSONResponse

# Returns a standard API response
def api_response(data, status=200):
    return JSONResponse(content=data, status_code=status)


def api_abort(message, code):
    print(message)
    raise HTTPException(status_code=code, detail={"error": message})


def api_ok(message="ok"):
    return api_response({'message': message})


# Validates a parameter
def validate(req, param, validator, is_required=True):
    if param not in req:
        if is_required:
            api_abort(f"Required parameter '{param}' is missing.", 400)
        else:
            return True
    if not validator(req[param]):
        api_abort(f"Value of '{param}' is invalid.", 400)
