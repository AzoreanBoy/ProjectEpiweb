---------- UNIVARIATE FEATURES --------
INSERT INTO feature (id, name, function_name, description, type, external)
VALUES (DEFAULT, 'Energy', '', '', 'uni', false),
       (DEFAULT, 'Hjorth', '', '', 'uni', false),
       (DEFAULT, 'ARModCoeff', '', '', 'uni', false),
       (DEFAULT, 'DecorrTime', '', '', 'uni', false),
       (DEFAULT, 'Entropy', '', '', 'uni', false),
       (DEFAULT, 'NonLinear', '', '', 'uni', false),
       (DEFAULT, 'RelPower', '', '', 'uni', false),
       (DEFAULT, 'SpecterEdge', '', '', 'uni', false),
       (DEFAULT, 'Statistic', '', '', 'uni', false),
       (DEFAULT, 'WaveletCoefficient', '', '', 'uni', false);


----------- MULTIVARIATE FEATURES --------------
INSERT INTO feature (id, name, function_name, description, type, external)
VALUES (DEFAULT, 'Coherence', '', '', 'multi', false),
       (DEFAULT, 'Correlation', '', '', 'multi', false),
       (DEFAULT, 'DirectedTransferFcn', '', '', 'multi', false),
       (DEFAULT, 'MeanPhaseCoherence', '', '', 'multi', false),
       (DEFAULT, 'MutualInformation', '', '', 'multi', false),
       (DEFAULT, 'PartialDirectedCoherence', '', '', 'multi', false);

---------- ECG FEATURES --------------
INSERT INTO feature (id, name, function_name, description, type, external)
VALUES (DEFAULT, 'R-RStatistics', '', '', 'ecg', false),
       (DEFAULT, 'BPMStatistics', '', '', 'ecg', false),
       (DEFAULT, 'SpectralAnalysis', '', '', 'ecg', false),
       (DEFAULT, 'ApproximateEntropy', '', '', 'ecg', false),
       (DEFAULT, 'SampleEntropy', '', '', 'ecg', false);


---------- Channels -----------
INSERT INTO channels (val)
VALUES ('FP1'),
       ('FP2'),
       ('F3'),
       ('F4'),
       ('C3'),
       ('C4'),
       ('P3'),
       ('P4'),
       ('O1'),
       ('O2'),
       ('F7'),
       ('F8'),
       ('T3'),
       ('T4'),
       ('T5'),
       ('T6'),
       ('Fz'),
       ('Cz'),
       ('Pz'),
       ('T1'),
       ('T2'),
       ('RS'),
       ('EOG1'),
       ('EOG2'),
       ('EMG'),
       ('ECG'),
       ('PHO');


---------- NORMALIZATION METHODS ------------
INSERT INTO
    NORMALIZATION_METHOD (NAME)
VALUES
    ('Z-Score'),
    ('[0,1]'),
    ('[-1,1]');


--------- Selection Methods ------------
INSERT INTO
	SELECTION_METHOD (ID, NAME)
VALUES
	('RFE', 'Recursive Feature Elimination'),
	('MRMR', 'minimum Redundancy - Maximum Relevance');

--------- Reduction Methods ------------
INSERT INTO
    REDUCTION_METHOD (ID, NAME)
VALUES
    ('PCA', 'Principal Component Analysis');

--------- Classification Methods ------------
INSERT INTO
    CLASSIFICATION_METHOD (ID, NAME)
VALUES
    ('SVM', 'Support Vector Machine');
