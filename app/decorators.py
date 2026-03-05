from django.shortcuts import redirect
from django.contrib import messages

from app.models import Study, hasaccess


def unauthenticatedUser(viewFunc):
    """
    Decorator to check if the user is authenticated
    """
    def wrapperFunc(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        else:
            return viewFunc(request, *args, **kwargs)

    return wrapperFunc


def studyAcessAllowed(viewFunc):
    """
    Decorator to check if the user has access to the study
    """
    def wrapperFunc(request, *args, **kwargs):
        if request.user.is_authenticated: # Check if the user is authenticated
            study = Study.objects.get(pk=kwargs['studyId']) # Get the study
            studiesshared = Study.objects.filter(idstudy__in=hasaccess.objects.filter(user=request.user).values("study")) # Get the studies shared with the user
            if (study.user == request.user) or (study in studiesshared): # Check if the user is the owner of the study or the study is shared with the user
                return viewFunc(request, *args, **kwargs) # Call the view function
            else: # If the user does not have access to the study
                messages.warning(request, 'You do not have access to this study')
                return redirect('index')
        else: # Check if the user is not authenticated
            return redirect('index')
    return wrapperFunc
