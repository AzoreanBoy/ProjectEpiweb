# to create a form around a model -> create fields based on a model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True



class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'shadow appearance-none border-white border-2 bg-zinc-900 text-white rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter your username'})
        self.fields['email'].widget.attrs.update({
            'class': 'shadow appearance-none border-white border-2 bg-zinc-900 text-white rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter your email'})
        self.fields['password1'].widget.attrs.update({
            'class': 'shadow appearance-none border-white border-2 bg-zinc-900 text-white rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter your password'})
        self.fields['password2'].widget.attrs.update({
            'class': 'shadow appearance-none border-white border-2 bg-zinc-900 text-white rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Re-Enter your password'})


# class UploadForm(forms.Form):
#     files = forms.FileField(required=True, widget=forms.ClearableFileInput(
#         attrs={'webkitdirectory': True, 'directory': True, 'required': True, 'multiple': True, 'mozdirectory': True,
#             'msdirectory': True, 'odirectory': True,
#             'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600'}))


# class UploadFilesForm(forms.Form):
#     files = forms.FileField(required=True, widget=forms.ClearableFileInput(
#         attrs={'webkitdirectory': True, 'directory': True, 'required': True, 'multiple': True, 'mozdirectory': True,
#             'msdirectory': True, 'odirectory': True,
#             'class': 'relative m-0 block w-full min-w-0 flex-auto rounded-lg border-2 border-solid border-slate-300 bg-clip-padding px-3 py-[0.32rem] text-base font-normal text-slate-700 transition duration-300 ease-in-out file:-mx-3 file:-my-[0.32rem] file:overflow-hidden file:rounded-none file:border-0 file:border-solid file:border-inherit file:bg-slate-800 file:px-3 file:py-[0.32rem] file:text-slate-700 file:transition file:duration-150 file:ease-in-out file:[border-inline-end-width:1px] file:[margin-inline-end:0.75rem] hover:file:bg-slate-200 hover:file:cursor-pointer focus:border-primary focus:text-slate-700 focus:shadow-te-primary focus:outline-none', }))

class UploadForm(forms.Form):
    files = forms.FileField(required=True, widget=MultipleFileInput(
        attrs={'webkitdirectory': True, 'directory': True, 'required': True,
               'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600'}
    ))

class UploadFilesForm(forms.Form):
    files = forms.FileField(required=True, widget=MultipleFileInput(
        attrs={'webkitdirectory': True, 'directory': True, 'required': True,
               'class': 'relative m-0 block w-full min-w-0 flex-auto rounded-lg border-2 border-solid border-slate-300 bg-clip-padding px-3 py-[0.32rem] text-base font-normal text-slate-700 transition duration-300 ease-in-out file:-mx-3 file:-my-[0.32rem] file:overflow-hidden file:rounded-none file:border-0 file:border-solid file:border-inherit file:bg-slate-800 file:px-3 file:py-[0.32rem] file:text-slate-700 file:transition file:duration-150 file:ease-in-out file:[border-inline-end-width:1px] file:[margin-inline-end:0.75rem] hover:file:bg-slate-200 hover:file:cursor-pointer focus:border-primary focus:text-slate-700 focus:shadow-te-primary focus:outline-none'}
    ))


class UploadExternalFeatureForm(forms.Form):
    CHOICES = (('uni', 'Univariate'), ('multi', 'Multivariate'), ('ecg', 'ECG'))
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': ' appearance-none border border-solid border-slate-300 bg-white text-slate-700 rounded-lg w-full py-[0.32rem] px-3 leading-normal focus:outline-none focus:shadow-outline mb-8',
        'placeholder': "Feature Name", }))
    function_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': ' appearance-none border border-solid border-slate-300 bg-white text-slate-700 rounded-lg w-full py-[0.32rem] px-3 leading-normal focus:outline-none focus:shadow-outline mb-8 text-base font-normal',
        'placeholder': "Function Name", }))
    type = forms.ChoiceField(choices=CHOICES, required=True, widget=forms.Select(attrs={
        'class': "appearence-none border border-solid border-slate-300 bg-white text-slate-700 rounded-lg w-full py-[0.32rem] px-3 leading-normal focus:outline-none focus:shadow-outline mb-8 text-base font-normal"}))
    file = forms.FileField(required=True, widget=forms.ClearableFileInput(attrs={'accept': ".py",
        'class': 'relative m-0 block w-full min-w-0 flex-auto rounded-lg border border-solid border-slate-300 bg-clip-padding px-3 py-[0.32rem] text-base font-normal text-slate-700 transition duration-300 ease-in-out file:-mx-3 file:-my-[0.32rem] file:overflow-hidden file:rounded-none file:border-4 file:border-solid file:border-inherit file:bg-slate-800 file:px-3 file:py-[0.32rem] file:text-slate-700 file:transition file:duration-150 file:ease-in-out file:[border-inline-end-width:1px] file:[margin-inline-end:0.75rem] hover:file:bg-slate-200 hover:file:cursor-pointer focus:border-primary focus:text-slate-700 focus:shadow-te-primary focus:outline-none', }))

    description = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'appearance-none border border-solid border-slate-300 bg-white text-slate-700 rounded-lg w-full py-[0.32rem] px-3 leading-normal focus:outline-none focus:shadow-outline mb-8',
    'placeholder': 'Insert a short description of your feature here...'}))
