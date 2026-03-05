from django.db import models

# DOMAINS

class InterictalPattern(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label = "epidb"
        managed = False
        db_table = "interictal_pattern"


class Pharmaceutical(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        app_label = "epidb"
        managed = False
        db_table = "pharmaceutical"

class FileFormat(models.Model):
    id = models.CharField(primary_key=True, max_length=3)
    value = models.CharField(max_length=255, blank=True, null=True)
    suffix = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'file_format'

class Assessment(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'assessment'

class Extent(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'extent'

# ORGANISATION INFORMATION
class Affiliation(models.Model):
    id = models.CharField(primary_key=True, max_length=5)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'affiliation'

class UserRole(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'user_role'

class DbUser(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(unique=True, max_length=16)
    affiliation = models.ForeignKey(Affiliation, models.DO_NOTHING, db_column='affiliation')

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'db_user'

# EEG EVENTS
class SeizureType(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'seizure_type'

class SeizurePattern(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'seizure_pattern'

class VigilanceState(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'vigilance_state'

class AnnotationCategory(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'annotation_category'

#ELECTRODES
class ElectrodeArrayType(models.Model):
    id = models.CharField(primary_key=True, max_length=5)
    value = models.CharField(max_length=50, blank=True, null=True)
    invasive = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_array_type'

class ElectrodeFocusRelation(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=75, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_focus_relation'

class ElectrodeFunctionType(models.Model):
    id = models.CharField(primary_key=True, max_length=3)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_function_type'

class ElectrodeSupplier(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_supplier'

class Artifact(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'artifact'

# ADMISSION
class Gender(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'gender'

class Hospital(models.Model):
    id = models.CharField(primary_key=True, max_length=5)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'hospital'

class Decision(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'decision'

class CognitiveScale(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'cognitive_scale'

class Heterotopia(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'heterotopia'

# SURGERY
class Callosotomy(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'callosotomy'

class ResectionResult(models.Model):
    id = models.CharField(primary_key=True, max_length=2)
    value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'resection_result'

class Tumor(models.Model):
    id = models.CharField(primary_key=True, max_length=3)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'tumor'

class Lesion(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'lesion'

class OutcomeEngel(models.Model):
    id = models.CharField(primary_key=True, max_length=4)
    value = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'outcome_engel'

class BrainRegion(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)
    descr = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brain_region'

class BrainSubRegion(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'brain_sub_region'

class Lateralisation(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    value = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'lateralisation'

class Localisation(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    description = models.CharField(max_length=255, blank=True, null=True)
    region = models.ForeignKey(BrainRegion, models.DO_NOTHING, db_column='region')
    sub_region = models.ForeignKey(BrainSubRegion, models.DO_NOTHING, db_column='sub_region')
    lateralisation = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='lateralisation')

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'localisation'

#_______________________
#   SCHEMA
#_______________________

class Patient(models.Model):
    
    patientcode = models.CharField(unique=True, max_length=32)
    gender = models.ForeignKey(Gender, models.DO_NOTHING, db_column='gender')
    onsetage = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'patient'

class Files(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    format = models.ForeignKey(FileFormat, models.DO_NOTHING, db_column='format', blank=True, null=True)
    length = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    create_ts = models.DateTimeField(blank=True, null=True)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'files'
        unique_together = (('name', 'path'),)

# ADMISSION SUBSET

class Admission(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, db_column='patient')
    adm_date = models.DateField(blank=True, null=True)
    age = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    hospital = models.ForeignKey('Hospital', models.DO_NOTHING, db_column='hospital', blank=True, null=True)
    presurgical = models.SmallIntegerField(blank=True, null=True)
    surgicaldecision = models.ForeignKey('Decision', on_delete=models.DO_NOTHING, db_column='surgicaldecision', blank=True, null=True)
    seeg = models.SmallIntegerField(blank=True, null=True)
    ieeg = models.SmallIntegerField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'admission'
        unique_together = (('patient', 'adm_date'),)

class Etiology(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    vascular_hypoxia = models.SmallIntegerField(blank=True, null=True)
    trauma = models.SmallIntegerField(blank=True, null=True)
    inflammation = models.SmallIntegerField(blank=True, null=True)
    malformation = models.SmallIntegerField(blank=True, null=True)
    hippocampal_sclerosis = models.SmallIntegerField(blank=True, null=True)
    degeneration = models.SmallIntegerField(blank=True, null=True)
    tumor = models.SmallIntegerField(blank=True, null=True)
    idiopathic = models.SmallIntegerField(blank=True, null=True)
    cns_surgery = models.SmallIntegerField(blank=True, null=True)
    genetic_risk = models.SmallIntegerField(blank=True, null=True)
    other = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'etiology'

class Spect(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    ictal_hyperfusion = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='ictal_hyperfusion', blank=True, null=True)
    interictal_hypofusion = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='interictal_hypofusion', blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'spect'

class Pet(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    hypometabolism = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hypometabolism', blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'pet'

class Cognitivefunction(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    test_date = models.DateField(blank=True, null=True)
    attention = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='attention', blank=True, null=True)
    verbal_declarat_memory = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='verbal_declarat_memory', blank=True, null=True)
    nonverbal_declarat_mem = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='nonverbal_declarat_mem', blank=True, null=True)
    language = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='language', blank=True, null=True)
    visuospatial_functions = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='visuospatial_functions', blank=True, null=True)
    executive_functions = models.ForeignKey(CognitiveScale, models.DO_NOTHING, db_column='executive_functions', blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'cognitivefunction'

class Mri(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    mri_date = models.DateField(blank=True, null=True)
    hippocampal_atrophy = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hippocampal_atrophy', blank=True, null=True)
    hippocampal_intensity_incr = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hippocampal_intensity_incr', blank=True, null=True)
    hippocampal_malrotation = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hippocampal_malrotation', blank=True, null=True)
    hippocampal_tumor = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hippocampal_tumor', blank=True, null=True)
    amygdala_atrophy = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='amygdala_atrophy', blank=True, null=True)
    amygdala_intensity_incr = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='amygdala_intensity_incr', blank=True, null=True)
    amygdala_tumor = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='amygdala_tumor', blank=True, null=True)
    temp_lobe_intensity_incr = models.SmallIntegerField(blank=True, null=True)
    gray_white_matter_blurring = models.SmallIntegerField(blank=True, null=True)
    cavernoma = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='cavernoma', blank=True, null=True)
    angioma = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='angioma', blank=True, null=True)
    aneurysma = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='aneurysma', blank=True, null=True)
    venous_dysplasia = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='venous_dysplasia', blank=True, null=True)
    dural_fistula = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='dural_fistula', blank=True, null=True)
    other_vessel_malformation = models.CharField(max_length=255, blank=True, null=True)
    tumor = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='tumor', blank=True, null=True)
    contrast_enhancement = models.SmallIntegerField(blank=True, null=True)
    cortical_dysplasia = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='cortical_dysplasia', blank=True, null=True)
    tubers = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='tubers', blank=True, null=True)
    heterotopia = models.ForeignKey(Heterotopia, models.DO_NOTHING, db_column='heterotopia', blank=True, null=True)
    polymicrogyria = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='polymicrogyria', blank=True, null=True)
    pachygyria = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='pachygyria', blank=True, null=True)
    lessencephaly = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='lessencephaly', blank=True, null=True)
    schizencephaly = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='schizencephaly', blank=True, null=True)
    micrencephaly = models.SmallIntegerField(blank=True, null=True)
    megalencephaly = models.SmallIntegerField(blank=True, null=True)
    hemimegalencephaly = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='hemimegalencephaly', blank=True, null=True)
    hypothalamic_hamartoma = models.SmallIntegerField(blank=True, null=True)
    other_cort_developm_malform = models.CharField(max_length=255, blank=True, null=True)
    contusion = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='contusion', blank=True, null=True)
    ischemic_lesion = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='ischemic_lesion', blank=True, null=True)
    intracerebral_bleeding = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='intracerebral_bleeding', blank=True, null=True)
    atrophy = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='atrophy', blank=True, null=True)
    arachnoid_cyst = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='arachnoid_cyst', blank=True, null=True)
    hydrocephalus = models.SmallIntegerField(blank=True, null=True)
    other_lesions = models.CharField(max_length=255, blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'mri'

class MriFiles(models.Model):
    id = models.OneToOneField(Admission, on_delete=models.CASCADE, db_column='id', primary_key=True)
    diagnosis = models.ForeignKey(Mri, models.DO_NOTHING, db_column='diagnosis')
    slice = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    image = models.ForeignKey(Files, models.DO_NOTHING, db_column='image')
    header = models.ForeignKey(Files, models.DO_NOTHING, db_column='header', blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'mri_files'

class Seizuretypefrequency(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission')
    type = models.ForeignKey(SeizureType, models.DO_NOTHING, db_column='type')
    frequency = models.FloatField()
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'seizuretypefrequency'
        unique_together = (('admission', 'type'),)

class Complication(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission')
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'complication'

class EegFocus(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission')
    localisation = models.ForeignKey('Localisation', models.DO_NOTHING, db_column='localisation')
    focus_number = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    ieeg_based = models.SmallIntegerField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'eeg_focus'

class Medication(models.Model):
    admission = models.ForeignKey(Admission, models.CASCADE, db_column='admission')
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    medicament = models.ForeignKey(Pharmaceutical, models.DO_NOTHING, db_column='medicament', blank=True, null=True)
    dosage = models.FloatField(blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'medication'

# SURGERY SUBSET
class Surgery(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission', blank=True, null=True)
    surgery_date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=2000, blank=True, null=True)
    callosotomy = models.ForeignKey(Callosotomy, models.DO_NOTHING, db_column='callosotomy', blank=True, null=True)
    mst = models.SmallIntegerField(blank=True, null=True)
    radiosurgery = models.SmallIntegerField(blank=True, null=True)
    mri_postop = models.ForeignKey(ResectionResult, models.DO_NOTHING, db_column='mri_postop', blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'surgery'

class Surgerycomplication(models.Model):
    id = models.OneToOneField(Surgery, on_delete=models.CASCADE, db_column='id', primary_key=True)
    infection = models.SmallIntegerField(blank=True, null=True)
    bleeding = models.SmallIntegerField(blank=True, null=True)
    infarction = models.SmallIntegerField(blank=True, null=True)
    early_seizures = models.SmallIntegerField(blank=True, null=True)
    electrolyte_disturbance = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'surgerycomplication'

class Histology(models.Model):
    id = models.OneToOneField(Surgery, on_delete=models.CASCADE, db_column='id', primary_key=True)
    tumor_category = models.ForeignKey(Tumor, models.DO_NOTHING, db_column='tumor_category', blank=True, null=True)
    tumor_description = models.CharField(max_length=255, blank=True, null=True)
    who_degree = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    cavernoma = models.SmallIntegerField(blank=True, null=True)
    av_malformation = models.SmallIntegerField(blank=True, null=True)
    capillary_teleengiecstasia = models.SmallIntegerField(blank=True, null=True)
    other_vessel_malformation = models.CharField(max_length=255, blank=True, null=True)
    focal_cortical_dysplasia = models.SmallIntegerField(blank=True, null=True)
    cortical_dysplasia = models.SmallIntegerField(blank=True, null=True)
    heterotopia = models.ForeignKey(Heterotopia, models.DO_NOTHING, db_column='heterotopia', blank=True, null=True)
    heterotopia_desc = models.CharField(max_length=255, blank=True, null=True)
    agyria = models.SmallIntegerField(blank=True, null=True)
    micropolygyria = models.SmallIntegerField(blank=True, null=True)
    porencephaly = models.SmallIntegerField(blank=True, null=True)
    ulegyria = models.SmallIntegerField(blank=True, null=True)
    other_cortical_malformation = models.CharField(max_length=255, blank=True, null=True)
    hippocampal_sclerosis = models.SmallIntegerField(blank=True, null=True)
    hippocampal_sclerosis_desc = models.CharField(max_length=255, blank=True, null=True)
    hamartoma = models.SmallIntegerField(blank=True, null=True)
    hamartoma_description = models.CharField(max_length=255, blank=True, null=True)
    inflammation_acute = models.SmallIntegerField(blank=True, null=True)
    inflammation_chronical = models.SmallIntegerField(blank=True, null=True)
    inflammation_description = models.CharField(max_length=255, blank=True, null=True)
    lesion_category = models.ForeignKey(Lesion, models.DO_NOTHING, db_column='lesion_category', blank=True, null=True)
    lesion_description = models.CharField(max_length=255, blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'histology'

class Surgerylocalisation(models.Model):
    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE, db_column='surgery')
    localisation = models.ForeignKey(Localisation, models.DO_NOTHING, db_column='localisation')

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'surgerylocalisation'
        unique_together = (('surgery', 'localisation'),)

class FollowUp(models.Model):
    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE, db_column='surgery')
    fup_date = models.DateField(blank=True, null=True)
    interval = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    outcome = models.ForeignKey(OutcomeEngel, models.DO_NOTHING, db_column='outcome')
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'follow_up'

# RECORDING SUBSET
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
        app_label='epidb'
        managed = False
        db_table = 'recording'

class Block(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording')
    eeg_file = models.ForeignKey('Files', on_delete=models.SET_NULL, db_column='eeg_file', blank=True, null=True)
    block_no = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    samples = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    sample_bytes = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    channels = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    factor = models.FloatField(blank=True, null=True)
    begin_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    gap = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'block'

class ElectrodeArray(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.ForeignKey(ElectrodeArrayType, on_delete=models.DO_NOTHING, db_column='type', blank=True, null=True)
    configuration = models.CharField(max_length=255, blank=True, null=True)
    implant_date = models.DateTimeField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_array'

class Electrode(models.Model):
    id = models.BigAutoField(primary_key=True)
    grid = models.ForeignKey(ElectrodeArray, on_delete=models.CASCADE, db_column='grid', blank=True, null=True)
    name = models.CharField(max_length=32, blank=True, null=True)
    moniker = models.CharField(max_length=32, blank=True, null=True)
    artifact = models.ForeignKey(Artifact, on_delete=models.DO_NOTHING, db_column='artifact', blank=True, null=True)
    focus_rel = models.ForeignKey(ElectrodeFocusRelation, on_delete=models.DO_NOTHING, db_column='focus_rel', blank=True, null=True)
    invasive = models.SmallIntegerField(blank=True, null=True)
    supplier = models.ForeignKey(ElectrodeSupplier, on_delete=models.DO_NOTHING, db_column='supplier', blank=True, null=True)
    coord_x = models.FloatField(blank=True, null=True)
    coord_y = models.FloatField(blank=True, null=True)
    coord_z = models.FloatField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode'

class ElectrodeUsage(models.Model):
    recording = models.ForeignKey('Recording', on_delete=models.CASCADE, db_column='recording', blank=True, null=True)
    electrode = models.ForeignKey(Electrode, on_delete=models.CASCADE, db_column='electrode', blank=True, null=True)
    grid = models.ForeignKey(ElectrodeArray, on_delete=models.SET_NULL, db_column='grid', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    position = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    function = models.ForeignKey(ElectrodeFunctionType, models.DO_NOTHING, db_column='function', blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'electrode_usage'

# EEG EVENTS SUBSET
class Seizure(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording', blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, db_column='block', blank=True, null=True)
    eeg_onset = models.DateTimeField(blank=True, null=True)
    clin_onset = models.DateTimeField(blank=True, null=True)
    first_eeg_change = models.DateTimeField(blank=True, null=True)
    first_clin_sign = models.DateTimeField(blank=True, null=True)
    eeg_offset = models.DateTimeField(blank=True, null=True)
    clin_offset = models.DateTimeField(blank=True, null=True)
    pattern = models.ForeignKey('SeizurePattern', models.DO_NOTHING, db_column='pattern', blank=True, null=True)
    classification = models.ForeignKey('SeizureType', models.DO_NOTHING, db_column='classification', blank=True, null=True)
    vigilance = models.ForeignKey('VigilanceState', models.DO_NOTHING, db_column='vigilance', blank=True, null=True)
    focus = models.ForeignKey(EegFocus, models.DO_NOTHING, db_column='focus', blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'seizure'

class Subclinicalevent(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording', blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, db_column='block', blank=True, null=True)
    onset_time = models.DateTimeField(blank=True, null=True)
    offset_time = models.DateTimeField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'subclinicalevent'

class Spike(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE, db_column='recording', blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, db_column='block', blank=True, null=True)
    type = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    pattern = models.ForeignKey(InterictalPattern, on_delete=models.DO_NOTHING, db_column='pattern', blank=True, null=True)
    amplit_max = models.ForeignKey(Electrode, on_delete=models.SET_NULL, db_column='amplit_max', blank=True, null=True)
    peak = models.DateTimeField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'spike'

class Propagation(models.Model):
    electrode = models.ForeignKey(Electrode, on_delete=models.CASCADE, db_column='electrode', blank=True, null=True)
    seizure = models.ForeignKey('Seizure', on_delete=models.CASCADE, db_column='seizure', blank=True, null=True)
    spike = models.ForeignKey('Spike', on_delete=models.CASCADE, db_column='spike', blank=True, null=True)
    origin = models.SmallIntegerField(blank=True, null=True, default=0)
    early = models.SmallIntegerField(blank=True, null=True, default=0)
    late = models.SmallIntegerField(blank=True, null=True, default=0)
    fieldext = models.SmallIntegerField(blank=True, null=True, default=0)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'propagation'

class Semiology(models.Model):
    seizure = models.ForeignKey(Seizure, models.DO_NOTHING, db_column='seizure')
    ts = models.DateTimeField(blank=True, null=True)
    elementary_auditory = models.SmallIntegerField(blank=True, null=True)
    complex_auditory = models.SmallIntegerField(blank=True, null=True)
    epigastric = models.SmallIntegerField(blank=True, null=True)
    gustatory = models.SmallIntegerField(blank=True, null=True)
    olfactory = models.SmallIntegerField(blank=True, null=True)
    somatosensory = models.SmallIntegerField(blank=True, null=True)
    visual = models.SmallIntegerField(blank=True, null=True)
    psychic = models.SmallIntegerField(blank=True, null=True)
    other_subjective_symptoms = models.CharField(max_length=50, blank=True, null=True)
    behavioral_arrest = models.SmallIntegerField(blank=True, null=True)
    staring = models.SmallIntegerField(blank=True, null=True)
    oral_automatisms = models.SmallIntegerField(blank=True, null=True)
    manual_automatisms = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='manual_automatisms', blank=True, null=True)
    atonia = models.SmallIntegerField(blank=True, null=True)
    tonic_posturing = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='tonic_posturing', blank=True, null=True)
    dystonic_posturing = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='dystonic_posturing', blank=True, null=True)
    grimacing = models.SmallIntegerField(blank=True, null=True)
    hypermotor_movements = models.SmallIntegerField(blank=True, null=True)
    restlessness = models.SmallIntegerField(blank=True, null=True)
    hypomotor = models.SmallIntegerField(blank=True, null=True)
    clonic_movements = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='clonic_movements', blank=True, null=True)
    myoclonic_movements = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='myoclonic_movements', blank=True, null=True)
    lid_myoclonus = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='lid_myoclonus', blank=True, null=True)
    eye_version = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='eye_version', blank=True, null=True)
    head_version = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='head_version', blank=True, null=True)
    body_version = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='body_version', blank=True, null=True)
    nystagmus = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='nystagmus', blank=True, null=True)
    sign_of_four = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='sign_of_four', blank=True, null=True)
    hypermotor = models.SmallIntegerField(blank=True, null=True)
    laughing = models.SmallIntegerField(blank=True, null=True)
    vocalisation = models.SmallIntegerField(blank=True, null=True)
    tongue_bite = models.SmallIntegerField(blank=True, null=True)
    other_motor_symptoms = models.SmallIntegerField(blank=True, null=True)
    other_motor_symptoms_desc = models.CharField(max_length=50, blank=True, null=True)
    negative_myoclonus = models.SmallIntegerField(blank=True, null=True)
    asystoly = models.SmallIntegerField(blank=True, null=True)
    bradycardia = models.SmallIntegerField(blank=True, null=True)
    tachycardia = models.SmallIntegerField(blank=True, null=True)
    extrasystoles = models.SmallIntegerField(blank=True, null=True)
    pallor = models.SmallIntegerField(blank=True, null=True)
    flush = models.SmallIntegerField(blank=True, null=True)
    piloarrection = models.SmallIntegerField(blank=True, null=True)
    hyperhydrosis = models.SmallIntegerField(blank=True, null=True)
    hypersalivation = models.SmallIntegerField(blank=True, null=True)
    vomiting = models.SmallIntegerField(blank=True, null=True)
    enuresis = models.SmallIntegerField(blank=True, null=True)
    encopresis = models.SmallIntegerField(blank=True, null=True)
    other_vegetative_symptoms = models.SmallIntegerField(blank=True, null=True)
    other_vegetative_symptoms_desc = models.CharField(max_length=100, blank=True, null=True)
    reactivity_nonverbal_stimuli = models.ForeignKey(Assessment, models.DO_NOTHING, db_column='reactivity_nonverbal_stimuli', blank=True, null=True)
    reactivity_verbal_stimuli = models.ForeignKey(Assessment, models.DO_NOTHING, db_column='reactivity_verbal_stimuli', blank=True, null=True)
    language_comprehension = models.ForeignKey(Assessment, models.DO_NOTHING, db_column='language_comprehension', blank=True, null=True)
    no_ictal_speech = models.SmallIntegerField(blank=True, null=True)
    ictal_complex_speech = models.SmallIntegerField(blank=True, null=True)
    ictal_stereotypic_speech = models.SmallIntegerField(blank=True, null=True)
    ictal_expressive_aphasia = models.SmallIntegerField(blank=True, null=True)
    ictal_perceptive_aphasia = models.SmallIntegerField(blank=True, null=True)
    other_ictal_aphasia = models.SmallIntegerField(blank=True, null=True)
    ictal_anomia = models.SmallIntegerField(blank=True, null=True)
    ictal_alexia = models.SmallIntegerField(blank=True, null=True)
    ictal_dysarthria = models.SmallIntegerField(blank=True, null=True)
    postictal_amnesia = models.ForeignKey(Extent, models.DO_NOTHING, db_column='postictal_amnesia', blank=True, null=True)
    postictal_anomia = models.SmallIntegerField(blank=True, null=True)
    postictal_expressive_aphasia = models.SmallIntegerField(blank=True, null=True)
    postictal_perceptive_aphasia = models.SmallIntegerField(blank=True, null=True)
    other_postictal_aphasia = models.SmallIntegerField(blank=True, null=True)
    postictal_dysarthria = models.SmallIntegerField(blank=True, null=True)
    postictal_alexia = models.SmallIntegerField(blank=True, null=True)
    postictal_psychic_alterations = models.SmallIntegerField(blank=True, null=True)
    postictal_sensory_disturbance = models.SmallIntegerField(blank=True, null=True)
    postictal_neglect = models.SmallIntegerField(blank=True, null=True)
    postictal_headache = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='postictal_headache', blank=True, null=True)
    postictal_restlessness = models.SmallIntegerField(blank=True, null=True)
    postictal_todds_paresis = models.ForeignKey(Lateralisation, models.DO_NOTHING, db_column='postictal_todds_paresis', blank=True, null=True)
    postictal_nose_rubbing = models.SmallIntegerField(blank=True, null=True)
    postictal_coughing = models.SmallIntegerField(blank=True, null=True)
    commentary = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        app_label='epidb'
        managed = False
        db_table = 'semiology'

# ANNOTATION SUBSET