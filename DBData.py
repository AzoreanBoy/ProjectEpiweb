import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EPIWEB.settings")
django.setup()

from app.models import Feature, SubFeature, NormalizationMethod, SelectionMethod, ReductionMethod, ClassificationMethod, \
    Channel


def populate_features():
    # UNIVARIATE FEATURES
    univariate_features = [
        {'name': 'Energy', 'type': Feature.Type.UNIVARIATE},
        {'name': 'Hjorth', 'type': Feature.Type.UNIVARIATE},
        {'name': 'ARModCoeff', 'type': Feature.Type.UNIVARIATE},
        {'name': 'DecorrTime', 'type': Feature.Type.UNIVARIATE},
        {'name': 'Entropy', 'type': Feature.Type.UNIVARIATE},
        {'name': 'NonLinear', 'type': Feature.Type.UNIVARIATE},
        {'name': 'RelPower', 'type': Feature.Type.UNIVARIATE},
        {'name': 'SpectreEdge', 'type': Feature.Type.UNIVARIATE},
        {'name': 'Statistic', 'type': Feature.Type.UNIVARIATE},
        {'name': 'WaveletCoefficient', 'type': Feature.Type.UNIVARIATE},
    ]

    for feature_data in univariate_features:
        Feature.objects.get_or_create(name=feature_data['name'], type=feature_data['type'])

    # MULTIVARIATE FEATURES
    multivariate_features = [
        {'name': 'Coherence', 'type': Feature.Type.MULTIVARIATE},
        {'name': 'Correlation', 'type': Feature.Type.MULTIVARIATE},
        {'name': 'DirectedTransferFcn', 'type': Feature.Type.MULTIVARIATE},
        {'name': 'MeanPhaseCoherence', 'type': Feature.Type.MULTIVARIATE},
        {'name': 'MutualInformation', 'type': Feature.Type.MULTIVARIATE},
        {'name': 'PartialDirectedCoherence', 'type': Feature.Type.MULTIVARIATE},
    ]

    for feature_data in multivariate_features:
        Feature.objects.get_or_create(name=feature_data['name'], type=feature_data['type'])

    # ECG FEATURES
    ecg_features = [
        {'name': 'R-RStatistics', 'type': Feature.Type.ECG},
        {'name': 'BPMStatistics', 'type': Feature.Type.ECG},
        {'name': 'SpectralAnalysis', 'type': Feature.Type.ECG},
        {'name': 'ApproximateEntropy', 'type': Feature.Type.ECG},
        {'name': 'SampleEntropy', 'type': Feature.Type.ECG},
    ]

    for feature_data in ecg_features:
        Feature.objects.get_or_create(name=feature_data['name'], type=feature_data['type'])


def populate_normalization_methods():
    normalization_methods = ['Z-Score', '[0,1]', '[-1,1]']

    for method_name in normalization_methods:
        NormalizationMethod.objects.get_or_create(name=method_name)


def populate_selection_methods():
    selection_methods = [
        ('RFE', 'Recursive Feature Elimination'),
        ('MRMR', 'minimum Redundancy - Maximum Relevance'),
    ]

    for method_id, method_name in selection_methods:
        SelectionMethod.objects.get_or_create(id=method_id, name=method_name)


def populate_reduction_methods():
    reduction_methods = [
        ('PCA', 'Principal Component Analysis'),
    ]

    for method_id, method_name in reduction_methods:
        ReductionMethod.objects.get_or_create(id=method_id, name=method_name)


def populate_classification_methods():
    classification_methods = [
        ('SVM', 'Support Vector Machine'),
    ]

    for method_id, method_name in classification_methods:
        ClassificationMethod.objects.get_or_create(id=method_id, name=method_name)


def populate_channels():
    channels_data = [
        'FP1', 'FP2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
        'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz', 'T1',
        'T2', 'RS', 'EOG1', 'EOG2', 'EMG', 'ECG', 'PHO'
    ]

    for channel_val in channels_data:
        Channel.objects.get_or_create(val=channel_val)


def populate_subfeatures():
    subfeatures_data = {
        # Subfeatures for each feature
        "Statistic"  : ["Mean", "Variance", "Skewness", "Kurtosis"],
        "RelPow"     : ["Delta", "Theta", "Alpha", "Beta", "Gamma"],
        "Hjorth"     : ["Mobility", "Complexity"],
        "Energy"     : ["Energy"],
        "DecorrTime" : ["DecorrTime"],
        "SpectreEdge": ["SEF", "EdgePower"],
        # Add more features/subfeatures here
    }
    for feature_name, subfeature_list in subfeatures_data.items():
        feature_obj = Feature.objects.get(name=feature_name)
        for subfeature_name in subfeature_list:
            subfeature_obj, created = SubFeature.objects.get_or_create(name=subfeature_name, feature=feature_obj)
            if created:
                print(f'Created SubFeature: {subfeature_obj}')


if __name__ == '__main__':
    # populate_features()
    # populate_normalization_methods()
    # populate_selection_methods()
    # populate_reduction_methods()
    # populate_classification_methods()
    # populate_channels()
    # populate_subfeatures()
    pass