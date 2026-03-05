from django.contrib.auth.models import User
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils import timezone  # Eu adicionei isto


class Channel(models.Model):
    val = models.CharField(max_length=5, primary_key=True)

    class Meta:
        db_table = 'channels'

    def __str__(self):
        return self.val


class NormalizationMethod(models.Model):
    name = models.CharField(primary_key=True, max_length=12)

    class Meta:
        db_table = 'normalization_method'
        managed = False

    def __str__(self):
        return self.name


class SelectionMethod(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'selection_method'
        managed = False

    def __str__(self):
        return self.id


class ReductionMethod(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'reduction_method'
        managed = False

    def __str__(self):
        return self.id


class ClassificationMethod(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'classification_method'

    def __str__(self):
        return self.id


class Options(models.Model):
    idoptions = models.AutoField(primary_key=True)
    name = models.CharField(max_length=512, null=False)
    value = models.CharField(max_length=512, null=False)

    class Meta:
        db_table = "options"
        unique_together = [["name", "value"]]

    def __str__(self):
        return f"{self.name} : {self.value}"


class Patient(models.Model):
    idpat = models.IntegerField(primary_key=True)
    idrecord = models.IntegerField(blank=True, null=True)
    uploadtime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=True, blank=True)

    class Meta:
        db_table = "patient"


class Event(models.Model):
    idevent = models.AutoField(primary_key=True)
    type = models.CharField(max_length=512, blank=True, null=True)
    eeg_onset = models.CharField(max_length=512, blank=True, null=True)
    eeg_onset_sec = models.CharField(max_length=512, blank=True, null=True)
    clin_onset = models.CharField(max_length=512, blank=True, null=True)
    clin_onset_sec = models.CharField(max_length=512, blank=True, null=True)
    eeg_offset = models.CharField(max_length=512, blank=True, null=True)
    eeg_offset_sec = models.CharField(max_length=512, blank=True, null=True)
    clin_offset = models.CharField(max_length=512, blank=True, null=True)
    clin_offset_sec = models.CharField(max_length=512, blank=True, null=True)
    pattern = models.CharField(max_length=512, blank=True, null=True)
    classification = models.CharField(max_length=512, blank=True, null=True)
    vigilance = models.CharField(max_length=512, blank=True, null=True)
    medicament = models.CharField(max_length=512, blank=True, null=True)
    dosage = models.CharField(max_length=512, blank=True, null=True)
    asystoly = models.CharField(max_length=512, blank=True, null=True)
    bradycardia = models.CharField(max_length=512, blank=True, null=True)
    tachycardia = models.CharField(max_length=512, blank=True, null=True)
    extrasystoles = models.CharField(db_column="extrasystoles_", max_length=512, blank=True, null=True)
    patient = models.ForeignKey("Patient", models.CASCADE, db_column="patient_idpat")
    file = models.FileField(upload_to="data/events/", blank=True, null=True)

    class Meta:
        db_table = "event"


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "data/raw/user_{0}/{1}/{2}".format(instance.patient.user.username, instance.patient.idpat, filename)


class Information(models.Model):
    idinfo = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=512, blank=True, null=True, default="tempfilename")
    startts = models.CharField(max_length=512, blank=True, null=True)
    stopts = models.CharField(max_length=512, blank=True, null=True)
    durationts = models.CharField(max_length=512, blank=True, null=True)
    nsamples = models.CharField(max_length=512, blank=True, null=True)
    sampfreq = models.CharField(max_length=512, blank=True, null=True)
    conversionfactor = models.CharField(max_length=512, blank=True, null=True)
    nchannels = models.CharField(max_length=512, blank=True, null=True)
    elecnames = models.CharField(max_length=512, blank=True, null=True)
    sampbytes = models.CharField(max_length=512, blank=True, null=True)
    patient = models.ForeignKey("Patient", models.CASCADE, db_column="patient_idpat", blank=True, null=True)
    headfile = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    datafile = models.FileField(blank=True, null=True)

    class Meta:
        db_table = "information"

    def delete(self, *args, **kwargs):
        # first, delete the file
        self.headfile.delete(save=False)
        self.datafile.delete(save=False)

        # now, delete the object
        super(Information, self).delete(*args, **kwargs)


class Feature(models.Model):
    class Type(models.TextChoices):
        UNIVARIATE = "uni"
        MULTIVARIATE = "multi"
        ECG = "ecg"

    name = models.CharField(max_length=50, null=False, blank=False)
    function_name = models.CharField(max_length=52, null=False)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=6, blank=False, null=False, choices=Type.choices, default=Type.UNIVARIATE)
    external = models.BooleanField(default=False)  # 0 - Internal Feature / 1 - External Feature

    class Meta:
        db_table = "feature"

    def __str__(self):
        if self.external:
            return f"External Feature - {self.name}"
        else:
            return f"{self.name}"


class SubFeature(models.Model):
    name = models.CharField(primary_key=True, max_length=128)
    feature = models.ForeignKey(Feature, models.CASCADE, db_column="feature", blank=True, null=True,
                                related_name="subfeatures")

    class Meta:
        db_table = "subfeature"
        managed = False

    def __str__(self):
        return self.name


class ExternalFeature(Feature):
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=False, blank=False)
    upload_date = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=512)

    class Meta:
        db_table = "external_feature"

    def __str__(self):
        return f"{self.name} Feature belonging to {self.user.username}"

    def file_name(self):
        return f"[{self.user.id}]{self.function_name}"


class Study(models.Model):
    class Type(models.TextChoices):
        EXTRACT = "extraction", "extraction"
        NORM = "normalization", "normalization"
        SELRED = "selection/reduction", "selectionreduction"
        CLASSIF = "classification", "classification"

    idstudy = models.AutoField(primary_key=True)
    datestudy = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=512, blank=True, null=True)
    completed = models.BooleanField(blank=True, null=True)
    directory = models.CharField(max_length=512, blank=True, null=True)
    type = models.CharField(max_length=512, blank=True, null=True, choices=Type.choices, default=Type.EXTRACT, )
    patient = models.ForeignKey(Patient, models.CASCADE, db_column="patient_idpat", blank=True, null=True)
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=True, blank=True)
    admission_EPIDB = models.IntegerField(blank=True,
                                          null=True)  # I added this line to link the study to the admission in the EPIDB database (its not possible to use a ForeignKey Django Does not allow cross database relationships)

    class Meta:
        db_table = "study"

    def __str__(self):
        return f"#{self.idstudy} -> {self.name} by {self.user.username}"

    def get_type(self):
        type_mapping = {
            self.Type.EXTRACT: "Extraction",
            self.Type.NORM   : "Normalization",
            self.Type.SELRED : "Selection/Reduction",
            self.Type.CLASSIF: "Classification"
        }
        return type_mapping[self.type]


class Extraction(models.Model):
    channels = models.CharField(max_length=512, blank=True, null=True)  # Only for Graphical Purposes
    # (Graphical Representation of data from Extraction Study uses this field) -
    # After Alteration of the graphiccal function, this field should be removed
    channs = models.ManyToManyField(Channel, blank=True)
    filter = models.CharField(max_length=512, blank=True, null=True)
    filter_cutoff = models.FloatField(blank=True, null=True)
    filter_order = models.IntegerField(blank=True, null=True)
    windowsize = models.CharField(max_length=512, blank=True, null=True)
    windowstep = models.CharField(max_length=512, blank=True, null=True)
    subfeats = models.CharField(max_length=512, blank=True, null=True)
    featsoptions = models.JSONField(blank=True, null=True)
    version = models.DateTimeField(auto_now=True)
    study = models.OneToOneField(Study, models.CASCADE, db_column="study_idstudy", primary_key=True)
    features = models.ManyToManyField(Feature, blank=True)
    feats = models.CharField(max_length=512, blank=True, null=True)  # Only for Graphical Purposes like channels,
    # after alteration of the graphical function, this field should be removed
    SPH = models.IntegerField() # Minutes
    SOP = models.IntegerField() # Minutes

    split_point = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "extraction"

    def __str__(self):
        return f"Extraction for Study #{self.study.idstudy}"


class Normalization(models.Model):
    version = models.DateTimeField(auto_now_add=True)
    method = models.ForeignKey(NormalizationMethod, models.DO_NOTHING, db_column="method", blank=True, null=True)
    model_dir = models.CharField(max_length=512, blank=True, null=True)
    study = models.OneToOneField(Study, models.CASCADE, db_column="study_idstudy", primary_key=True)
    extraction_study = models.ForeignKey(Extraction, models.CASCADE, db_column="extraction_study_idstudy", blank=True,
                                         null=True, )

    class Meta:
        db_table = "normalization"


class SelectionReduction(models.Model):
    features = models.ManyToManyField(Feature, blank=True)
    feats = models.TextField(blank=True, null=True)
    selection_method = models.CharField(max_length=32, blank=True, null=True)
    reduction_method = models.CharField(max_length=32, blank=True, null=True)
    methodoptions = models.CharField(max_length=2000, blank=True, null=True)
    methodoptions2 = models.ManyToManyField(Options, blank=True)
    version = models.DateTimeField(auto_now=True)
    study = models.OneToOneField("Study", models.CASCADE, db_column="study_idstudy", primary_key=True)
    extraction_study = models.ForeignKey(Extraction, models.CASCADE, db_column="extraction_study_idstudy", blank=True,
                                         null=True, )
    normalization_study = models.ForeignKey(Normalization, models.CASCADE, db_column="normalization_study_idstudy",
                                            blank=True, null=True, )
    model_dir = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        db_table = "selection_reduction"

    def __str__(self):
        return f"Selection/Reduction for Study #{self.study.idstudy}"

    @property
    def from_study(self):
        return self.extraction_study if self.extraction_study is not None else self.normalization_study


class Classification(models.Model):
    features = models.ManyToManyField(Feature, blank=True)
    feats = models.TextField(blank=True, null=True)
    method = models.CharField(max_length=512, blank=True, null=True)
    methodoptions = models.CharField(max_length=512, blank=True, null=True)
    
    # Metrics
        # Model Related
    accuracy = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    fpr = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    recall = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    precision = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    f1_score = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    f2_score = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    
        # Alarm Related
    alarm_sensitivity = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    alarm_fpr = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=5)
    # End of Metrics
    
    version = models.DateTimeField(auto_now=True)
    study = models.OneToOneField(Study, models.CASCADE, db_column="study_idstudy", primary_key=True)

    extraction_study = models.ForeignKey(Extraction, models.CASCADE, db_column="extraction_study_idstudy", blank=True,
                                         null=True, )
    normalization_study = models.ForeignKey(Normalization, models.CASCADE, db_column="normalization_study_idstudy",
                                            blank=True, null=True, )
    selection_reduction_study = models.ForeignKey(SelectionReduction, models.CASCADE,
                                                  db_column="selection_reduction_study_idstudy", blank=True,
                                                  null=True, )
    patient = models.ForeignKey(Patient, models.CASCADE, db_column="patient_idpat", blank=True, null=True)

    class Meta:
        db_table = "classification"

    def __str__(self):
        return f"Classification for Study #{self.study.idstudy}"

    @property
    def from_study(self):
        return self.extraction_study or self.normalization_study or self.selection_reduction_study

    @property
    def origin_extraction_study(self):
        if self.extraction_study is not None:
            # ORIGIN IS EXTRACTION
            return self.extraction_study
        elif self.normalization_study is not None:
            # ORIGIN IS NORMALIZATION
            return self.normalization_study.extraction_study
        elif self.selection_reduction_study is not None:
            # ORIGIN IS SELECTION REDUCTION
            if self.selection_reduction_study.extraction_study is not None:
                # SELECTION REDUCTION HAS EXTRACTION AS ORIGIN
                return self.selection_reduction_study.extraction_study
            elif self.selection_reduction_study.normalization_study is not None:
                # SELECTION REDUCTION HAS NORMALIZATION AS ORIGIN
                return self.selection_reduction_study.normalization_study.extraction_study
            else:
                return None
        else:
            return None


class Notification(models.Model):
    idnot = models.AutoField(primary_key=True)
    datenot = models.DateTimeField(auto_now_add=True)
    consumed = models.BooleanField()
    description = models.CharField(max_length=512)
    datafield = models.BinaryField()
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=True, blank=True)
    study = models.ForeignKey("Study", models.CASCADE, db_column="study_idstudy", null=True, blank=True)

    class Meta:
        db_table = "notification"

    def __str__(self):
        return self.datenot.strftime("%d/%m/%Y %H:%M") + ":     " + self.description


class Comment(models.Model):
    idcom = models.AutoField(primary_key=True)
    datecom = models.DateTimeField()
    content = models.TextField()
    patient = models.ForeignKey("Patient", models.CASCADE, db_column="patient_idpat", blank=True, null=True)
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=True, blank=True)
    study = models.ForeignKey("Study", models.CASCADE, db_column="study_idstudy", null=True, blank=True)

    class Meta:
        db_table = "comment"

    def __str__(self):
        return (self.datecom.strftime("%d/%m/%Y %H:%M") + ":     " + self.content + "    by " + self.user.username)


class hasaccess(models.Model):
    user = models.ForeignKey(User, models.CASCADE, db_column="user_iduser", null=True, blank=True)
    study = models.ForeignKey("Study", models.CASCADE, db_column="study_idstudy", null=True, blank=True)
    patient = models.ForeignKey("Patient", models.CASCADE, db_column="patient_idpat", blank=True, null=True)
    since = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [UniqueConstraint(fields=["user", "study"], name="unique_with_patient"),
                       UniqueConstraint(fields=["user", "patient"], name="unique_without_study"), ]
        db_table = "hasaccess"

    def __str__(self):
        if self.study:
            return (self.study.name + " by " + self.study.user.username + " shared with  " + self.user.username)
        else:
            return ("Patient " + str(
                    self.patient.idpat) + " by " + self.patient.user.username + " shared with  " + self.user.username)


##################################################################################################
####                    EPIDB MODELS                                                          ####
##################################################################################################

# DOMAIN
class Gender(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'gender'


class Hospital(models.Model):
    id = models.CharField(primary_key=True, max_length=5)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'hospital'


class Decision(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'decision'


class BrainRegion(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)
    descr = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'brain_region'


class BrainSubRegion(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'brain_sub_region'


class Lateralisation(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'lateralisation'


class Localisation(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    description = models.CharField(max_length=255, blank=True, null=True)
    region = models.ForeignKey(BrainRegion, models.DO_NOTHING, db_column='region')
    sub_region = models.ForeignKey(BrainSubRegion, models.DO_NOTHING, db_column='sub_region')
    lateralisation = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='lateralisation')

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'localisation'


class FileFormat(models.Model):
    id = models.CharField(primary_key=True, max_length=3)
    value = models.CharField(max_length=255, blank=True, null=True)
    suffix = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'file_format'


class Files(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    format = models.ForeignKey(FileFormat, models.DO_NOTHING, db_column='format', blank=True, null=True)
    length = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    create_ts = models.DateTimeField(blank=True, null=True)
    checksum = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'files'
        unique_together = (('name', 'path'),)


class SeizureType(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'seizure_type'


class SeizurePattern(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'seizure_pattern'


class VigilanceState(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'vigilance_state'


# Models
class PatientEPI(models.Model):
    patientcode = models.CharField(unique=True, max_length=32)
    gender = models.ForeignKey(Gender, models.DO_NOTHING, db_column='gender')
    onsetage = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'patient'


class Admission(models.Model):
    patient = models.ForeignKey(PatientEPI, on_delete=models.CASCADE, db_column='patient')
    adm_date = models.DateField(blank=True, null=True)
    age = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    hospital = models.ForeignKey(Hospital, models.DO_NOTHING, db_column='hospital', blank=True, null=True)
    presurgical = models.SmallIntegerField(blank=True, null=True)
    surgicaldecision = models.ForeignKey(Decision, on_delete=models.DO_NOTHING, db_column='surgicaldecision',
                                         blank=True, null=True)
    seeg = models.SmallIntegerField(blank=True, null=True)
    ieeg = models.SmallIntegerField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'admission'
        unique_together = (('patient', 'adm_date'),)


class Recording(models.Model):
    str_id = models.CharField(unique=True, max_length=32, blank=True, null=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission', blank=True, null=True)
    begin_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    duration = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    blocks = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    channels = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    sample_rate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    backgrhythm = models.FloatField(blank=True, null=True)
    eegslowing = models.ForeignKey(Localisation, models.DO_NOTHING, db_column='eegslowing', blank=True, null=True)
    ieegslowing = models.ForeignKey(Localisation, models.DO_NOTHING, db_column='ieegslowing', blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'recording'


class Block(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording')
    eeg_file = models.ForeignKey(Files, on_delete=models.SET_NULL, db_column='eeg_file', blank=True, null=True)
    block_no = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    samples = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    sample_bytes = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    channels = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    factor = models.FloatField(blank=True, null=True)
    begin_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    gap = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'block'


class EegFocus(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission')
    localisation = models.ForeignKey(Localisation, models.DO_NOTHING, db_column='localisation')
    focus_number = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    ieeg_based = models.SmallIntegerField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'eeg_focus'


class Seizure(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording', blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, db_column='block', blank=True, null=True)
    eeg_onset = models.DateTimeField(blank=True, null=True)
    clin_onset = models.DateTimeField(blank=True, null=True)
    first_eeg_change = models.DateTimeField(blank=True, null=True)
    first_clin_sign = models.DateTimeField(blank=True, null=True)
    eeg_offset = models.DateTimeField(blank=True, null=True)
    clin_offset = models.DateTimeField(blank=True, null=True)
    pattern = models.ForeignKey(SeizurePattern, models.DO_NOTHING, db_column='pattern', blank=True, null=True)
    classification = models.ForeignKey(SeizureType, models.DO_NOTHING, db_column='classification', blank=True,
                                       null=True)
    vigilance = models.ForeignKey(VigilanceState, models.DO_NOTHING, db_column='vigilance', blank=True, null=True)
    focus = models.ForeignKey(EegFocus, models.DO_NOTHING, db_column='focus', blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label = 'epidb'
        managed = False
        db_table = 'seizure'
