from django.shortcuts import render


def not_found(request, exception=None):
    context = {
        "exception": exception
    }
    return render(request, 'errors/error404.html')


def bad_request(request, exception=None):
    context = {
        "exception": exception
    }
    return render(request, 'errors/error400.html', context)


def server_error(request, exception=None):
    context = {
        "exception": exception
    }
    return render(request, 'errors/error500.html', context)
