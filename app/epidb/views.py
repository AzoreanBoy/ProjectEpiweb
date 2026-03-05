from django.http import HttpResponse

from .modelEPI import *
def test_epi(request):
    patient = Patient.objects.all()
    s = ""
    for pat in patient:
        s += f"{pat.patientcode} - {pat.gender.value}"
        s += "<br>"
    return HttpResponse(s)
