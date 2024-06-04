from rest_framework.renderers import JSONRenderer

class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context['response'].status_code
        response = {
            "success": True,
            "code": status_code,
            "data": data,
            "message": None,
        }

        if not str(status_code).startswith('2'):
            response["success"] = False
            response["data"] = None
            try:
                if isinstance(data, dict):
                    first_error_object = list(data.values())[0]  
                    if isinstance(first_error_object, list):
                        error_message = first_error_object[0]
                    else:
                        error_message = first_error_object
                else:
                    error_message = data["detail"]
            except:
                error_message =''
            response["message"] = error_message
        return super(CustomRenderer,self).render(response,accepted_media_type,renderer_context)
        
