from rest_framework.views import exception_handler
from rest_framework.response import Response 
from rest_framework import status 


def custom_exception_handler(exc,context):
    '''
      Make Every Response Looks Same
    {
    success:false,
    error:{
        code:'error_code',
        message:'error message '
        fields:{'error field':'error field error message' }}} eg fields:{'confirm_password':'password does not match'}
    '''
    response = exception_handler(exc , context)

    if response is not None:
        error_payload = {
            "success" : False,
            "error" : {
                'code' :_get_error_code(response.status_code),
                'message' : _extract_message(response.data)
            }
        }

        #field level details for validation errors 
        if response.status_code == status.HTTP_400_BAD_REQUEST and isinstance(response.data,dict):
            error_payload['error']['fields']  = response.data 

        response.data=error_payload

    return response    


def _get_error_code(status_code):
    return {
        400: "validation_error",
        401: "authentication_error",
        403: "permission_denied",
        404: "not_found",
        429: "throttled",
    }.get(status_code, "error")


def _extract_message(data):
    if isinstance(data,dict):
        if 'detail' in data:
            return str(data['detail'])
        
        if 'non_field_errors' in data:
            errs = data['non_field_errors']
            return errs[0] if errs else 'Validation error.'
        
        for field,errors in data.items():
            if isinstance(errors,list) and errors:
                return f"{field}:{errors[0]}"
    
    if isinstance(data,list) and data:
        return str(data[0])
    
    return str(data)