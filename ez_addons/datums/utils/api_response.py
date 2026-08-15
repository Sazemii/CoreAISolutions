from odoo.http import request

def format_api_response(success=True, message="", data=None, pagination=None, meta=None):
    """
    Global function to format API responses in standardized format
    
    Args:
        success (bool): Whether the operation was successful
        message (str): Response message
        data (list/dict): Response data
        pagination (dict): Pagination information (optional)
        meta (dict): Extra metadata (e.g. counts, source breakdown) (optional)
    
    Returns:
        dict: Formatted response structure
    """
    if data is None:
        data = []
    
    # if pagination is None:
    #     if isinstance(data, list):
    #         pagination = {
    #             "total_pages": 1,
    #             "per_page": len(data),
    #             "curr_page": 1,
    #             "prev_page": False,
    #             "next_page": False,
    #             "count": len(data)
    #         }
    #     else:
    #         pagination = {
    #             "total_pages": 0,
    #             "per_page": 0,
    #             "curr_page": 1,
    #             "prev_page": False,
    #             "next_page": False,
    #             "count": 0
    #         }
    
    response = {
        "settings": {
            "success": 1 if success else 0,
            "message": message,
        },
        "data": data
    }

    if meta is not None:
        response["meta"] = meta
    
    return response

def make_json_response(response_dict):
    """
    Wrapper function to create JSON response using Odoo's request object
    
    Args:
        response_dict (dict): Response dictionary
    
    Returns:
        Odoo JSON response object
    """
    return request.make_json_response(response_dict)
