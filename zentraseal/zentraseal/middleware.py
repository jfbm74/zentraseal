class AllowPDFInFrameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Permitir embeber PDFs en frames si la URL es para un PDF
        if request.path.startswith('/media/secured/') and request.path.endswith('.pdf'):
            # Eliminar completamente la cabecera X-Frame-Options para permitir embeber en iframe
            if 'X-Frame-Options' in response:
                del response['X-Frame-Options']
        
        return response