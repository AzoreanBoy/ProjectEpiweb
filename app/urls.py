from django.urls import path, re_path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("test/", views.test, name="test"),
    # path('epidb/', include('app.epidb.urls')),
    # LOGIN/REGISTER USER SYSTEM
    path("login/", views.loginUser, name="loginUser"),
    path("logout/", views.logoutUser, name="logoutUser"),
    # RESET PASSWORD
    # submit email form
    path(
        "resetpass/", auth_views.PasswordResetView.as_view(), name="reset_password"
    ),  # success message sent by email
    path(
        "reset_password_sent/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    # email sent to reset pass
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # success
    path(
        "reset_password_complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # HOME PAGE for unauthenticated users
    path("epiweb", views.landing, name="landing"),  # HOME PAGE for authenticated users
    path("", views.index, name="index"),  # NOTIFICATIONS SYSTEM
    path("getnotifications/", views.notifications, name="notifications"),
    path("clearnotifications/", views.clearnotifications, name="clearnotifications"),
    re_path(r"^checkTask/(?P<tid>[0-9]+)/?$", views.checkTask, name="checkTask"),
    re_path(
        r"^checkTaskResult/(?P<tid>[0-9]+)/?$",
        views.checkTaskResult,
        name="checkTaskResult",
    ),  # PATIENT
    re_path(r"^patient/(?P<idpat>[0-9]+)/?$", views.patient, name="patient"),
    re_path(
        r"^plotpatient/(?P<idpat>[0-9]+)/(?P<step>[0-9]+)/(?P<window>[0-9]+)?$",
        views.plotRaw,
        name="plotpatient",
    ),
    re_path(
        r"^plotpatientAsync/(?P<idpat>[0-9]+)?$",
        views.plotRawAsync,
        name="plotpatientAsync",
    ),
    re_path(
        r"^plotevent/(?P<idevent>[0-9]+)/(?P<step>[0-9]+)?$",
        views.plotEvent,
        name="plotevent",
    ),
    path("filterplot/", views.filterplot, name="filterplot"),  # DATA
    path("data/<str:option>/", views.datav2, name="datav2"),
    path("confirmUpload/", views.confirmUpload, name="confirmUpload"),
    path(
        "cancelUpload/", views.cancelUpload, name="canceluploadData"
    ),  # EXTRACTION STUDY
    re_path(r"^create/(?P<idpat>[0-9]+)/?$", views.createStudy, name="createStudy"),
    path("create/", views.createStudyAsync, name="createStudyAsync"),
    path("extractFeat/", views.extractingFeatures, name="extractFeat"),
    re_path(
        r"^extractionStudy/(?P<studyId>[0-9]+)/?$",
        views.extractionStudyPage,
        name="extractionStudy",
    ),
    # PLOT FEATURE
    re_path(
        r"^plotfeature/(?P<studyId>[0-9]+)/(?P<stepminutes>[0-9]+)/(?P<window>[0-9]+)?$",
        views.plotFeature,
        name="plotFeature",
    ),
    re_path(
        r"^plotFeatureAsync/(?P<studyId>[0-9]+)?$",
        views.plotFeatureAsync,
        name="plotFeatureAsync",
    ),
    # TRAIN TEST SPLIT
    path("trainTestSplit/<int:studyId>", views.train_test_split, name="trainTestSplit"),
    # NORMALIZATION STUDY
    path(
        "createnormalization/<int:studyId>",
        views.createNormalization,
        name="createNormalizationStudy",
    ),
    path(
        "normalizationStudy/<int:studyId>",
        views.normalizationStudyPage,
        name="normalizationStudy",
    ),
    # SELECTION REDUCTION STUDY
    re_path(
        r"^createselectionreduction/(?P<studyId>[0-9]+)/?$",
        views.createSelRed,
        name="createStudySelRed",
    ),
    path(
        "createselectionreduction/", views.createSelRedAsync, name="createSelRedAsync"
    ),
    path("selred/", views.selectingreducing, name="selRed"),
    re_path(
        r"^selredStudy/(?P<studyId>[0-9]+)/?$",
        views.selredStudyPage,
        name="selredStudy",
    ),
    # CLASSIFICATION STUDY
    re_path(
        r"^createclassification/(?P<studyId>[0-9]+)/?$",
        views.createClassification,
        name="createStudyClassification",
    ),
    path(
        "createclassification/",
        views.createClassificationAsync,
        name="createClassificationAsync",
    ),
    path("classification/", views.classifying, name="classification"),
    path(
        "classificationStudy/<int:studyId>",
        views.classificationStudyPage,
        name="classificationStudy",
    ),
    # POST PROCESSING STUDY
    path(
        "createpostprocessing/<int:studyId>",
        views.postprocessing,
        name="PostProcessingStudy",
    ),
    # STUDY PAGE REDIRECT
    path("study/<int:studyId>", views.studyPage, name="studyPage"),
    # STUDY PAGES COMMENTS
    path("deletecomment/", views.deleteComment, name="deleteComment"),  # Upload Feature
    path("uploadFeature/", views.uploadExternalFeature, name="uploadFeature"),
]
