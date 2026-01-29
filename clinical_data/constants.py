"""
CIEL (Columbia International eHealth Laboratory) code mappings for OpenMRS compatibility.
These codes are widely used in African healthcare systems and ensure interoperability
with OpenMRS implementations.

Reference: https://openconceptlab.org/orgs/CIEL/
"""

# Code System URLs
CIEL_SYSTEM = 'http://openconceptlab.org/orgs/CIEL/sources/CIEL'
ICD10_SYSTEM = 'http://hl7.org/fhir/sid/icd-10-cm'
UCUM_SYSTEM = 'http://unitsofmeasure.org'

# ============================================================================
# VITAL SIGNS - CIEL Codes
# ============================================================================

CIEL_VITALS = {
    'systolic_bp': {
        'code': '5085',
        'display': 'Systolic blood pressure',
        'unit': 'mmHg',
        'normal_low': 90,
        'normal_high': 120,
    },
    'diastolic_bp': {
        'code': '5086',
        'display': 'Diastolic blood pressure',
        'unit': 'mmHg',
        'normal_low': 60,
        'normal_high': 80,
    },
    'heart_rate': {
        'code': '5087',
        'display': 'Pulse',
        'unit': 'bpm',
        'normal_low': 60,
        'normal_high': 100,
    },
    'body_temp': {
        'code': '5088',
        'display': 'Temperature (C)',
        'unit': 'Cel',
        'normal_low': 36.5,
        'normal_high': 37.5,
    },
    'respiratory_rate': {
        'code': '5242',
        'display': 'Respiratory rate',
        'unit': 'breaths/min',
        'normal_low': 12,
        'normal_high': 20,
    },
    'blood_glucose': {
        'code': '887',
        'display': 'Glucose',
        'unit': 'mg/dL',
        'normal_low': 70,
        'normal_high': 140,
    },
    'weight': {
        'code': '5089',
        'display': 'Weight (kg)',
        'unit': 'kg',
    },
    'height': {
        'code': '5090',
        'display': 'Height (cm)',
        'unit': 'cm',
    },
    'bmi': {
        'code': '1342',
        'display': 'Body mass index',
        'unit': 'kg/m2',
        'normal_low': 18.5,
        'normal_high': 24.9,
    },
    'oxygen_saturation': {
        'code': '5092',
        'display': 'Oxygen saturation',
        'unit': '%',
        'normal_low': 95,
        'normal_high': 100,
    },
}

# ============================================================================
# COMMON CONDITIONS - CIEL + ICD-10 Dual Coding
# ============================================================================

CIEL_CONDITIONS = {
    # Cardiovascular
    'hypertension': {
        'ciel': '117399',
        'icd10': 'I10',
        'display': 'Hypertension',
    },
    'heart_disease': {
        'ciel': '119270',
        'icd10': 'I51.9',
        'display': 'Heart disease',
    },
    'heart_failure': {
        'ciel': '139071',
        'icd10': 'I50.9',
        'display': 'Heart failure',
    },
    'stroke': {
        'ciel': '111103',
        'icd10': 'I63.9',
        'display': 'Stroke',
    },

    # Endocrine & Metabolic
    'diabetes_type1': {
        'ciel': '142474',
        'icd10': 'E10.9',
        'display': 'Type 1 diabetes mellitus',
    },
    'diabetes_type2': {
        'ciel': '119481',
        'icd10': 'E11.9',
        'display': 'Type 2 diabetes mellitus',
    },
    'diabetes': {
        'ciel': '119481',
        'icd10': 'E11.9',
        'display': 'Diabetes mellitus',
    },
    'obesity': {
        'ciel': '114413',
        'icd10': 'E66.9',
        'display': 'Obesity',
    },
    'hyperthyroidism': {
        'ciel': '145439',
        'icd10': 'E05.9',
        'display': 'Hyperthyroidism',
    },
    'hypothyroidism': {
        'ciel': '117698',
        'icd10': 'E03.9',
        'display': 'Hypothyroidism',
    },

    # Infectious Diseases
    'malaria': {
        'ciel': '115491',
        'icd10': 'B54',
        'display': 'Malaria',
    },
    'tuberculosis': {
        'ciel': '112141',
        'icd10': 'A15.9',
        'display': 'Tuberculosis',
    },
    'hiv': {
        'ciel': '138405',
        'icd10': 'B24',
        'display': 'HIV disease',
    },
    'pneumonia': {
        'ciel': '114100',
        'icd10': 'J18.9',
        'display': 'Pneumonia',
    },
    'typhoid': {
        'ciel': '112234',
        'icd10': 'A01.0',
        'display': 'Typhoid fever',
    },
    'hepatitis_b': {
        'ciel': '112786',
        'icd10': 'B18.1',
        'display': 'Chronic viral hepatitis B',
    },
    'hepatitis_c': {
        'ciel': '145706',
        'icd10': 'B18.2',
        'display': 'Chronic viral hepatitis C',
    },
    'cholera': {
        'ciel': '110488',
        'icd10': 'A00.9',
        'display': 'Cholera',
    },
    'dengue': {
        'ciel': '123120',
        'icd10': 'A90',
        'display': 'Dengue fever',
    },

    # Respiratory
    'asthma': {
        'ciel': '121375',
        'icd10': 'J45.9',
        'display': 'Asthma',
    },
    'copd': {
        'ciel': '145249',
        'icd10': 'J44.9',
        'display': 'Chronic obstructive pulmonary disease',
    },
    'bronchitis': {
        'ciel': '147247',
        'icd10': 'J40',
        'display': 'Bronchitis',
    },

    # Gastrointestinal
    'diarrhea': {
        'ciel': '142412',
        'icd10': 'A09',
        'display': 'Diarrhea',
    },
    'gastritis': {
        'ciel': '145978',
        'icd10': 'K29.7',
        'display': 'Gastritis',
    },
    'peptic_ulcer': {
        'ciel': '139316',
        'icd10': 'K27.9',
        'display': 'Peptic ulcer',
    },

    # Musculoskeletal
    'arthritis': {
        'ciel': '116558',
        'icd10': 'M19.90',
        'display': 'Arthritis',
    },
    'osteoarthritis': {
        'ciel': '123939',
        'icd10': 'M19.90',
        'display': 'Osteoarthritis',
    },
    'rheumatoid_arthritis': {
        'ciel': '145454',
        'icd10': 'M06.9',
        'display': 'Rheumatoid arthritis',
    },

    # Renal
    'kidney_disease': {
        'ciel': '145438',
        'icd10': 'N28.9',
        'display': 'Kidney disease',
    },
    'chronic_kidney_disease': {
        'ciel': '142412',
        'icd10': 'N18.9',
        'display': 'Chronic kidney disease',
    },
    'uti': {
        'ciel': '111633',
        'icd10': 'N39.0',
        'display': 'Urinary tract infection',
    },

    # Neurological
    'epilepsy': {
        'ciel': '155',
        'icd10': 'G40.9',
        'display': 'Epilepsy',
    },
    'migraine': {
        'ciel': '129558',
        'icd10': 'G43.9',
        'display': 'Migraine',
    },
    'neuropathy': {
        'ciel': '118983',
        'icd10': 'G62.9',
        'display': 'Neuropathy',
    },

    # Mental Health
    'depression': {
        'ciel': '119537',
        'icd10': 'F32.9',
        'display': 'Depression',
    },
    'anxiety': {
        'ciel': '121543',
        'icd10': 'F41.9',
        'display': 'Anxiety disorder',
    },
    'psychosis': {
        'ciel': '115835',
        'icd10': 'F29',
        'display': 'Psychosis',
    },

    # Hematologic
    'anemia': {
        'ciel': '121629',
        'icd10': 'D64.9',
        'display': 'Anemia',
    },
    'sickle_cell': {
        'ciel': '117703',
        'icd10': 'D57.1',
        'display': 'Sickle cell disease',
    },

    # Dermatologic
    'eczema': {
        'ciel': '116155',
        'icd10': 'L30.9',
        'display': 'Eczema',
    },
    'psoriasis': {
        'ciel': '119021',
        'icd10': 'L40.9',
        'display': 'Psoriasis',
    },

    # Pregnancy & Reproductive
    'pregnancy': {
        'ciel': '1065',
        'icd10': 'Z33.1',
        'display': 'Pregnancy',
    },
    'gestational_diabetes': {
        'ciel': '113858',
        'icd10': 'O24.4',
        'display': 'Gestational diabetes mellitus',
    },
    'preeclampsia': {
        'ciel': '114244',
        'icd10': 'O14.9',
        'display': 'Pre-eclampsia',
    },
}

# ============================================================================
# COMMON MEDICATIONS - CIEL Codes
# ============================================================================

CIEL_MEDICATIONS = {
    # Analgesics & Anti-inflammatories
    'paracetamol': {'code': '70116', 'display': 'Paracetamol'},
    'ibuprofen': {'code': '5356', 'display': 'Ibuprofen'},
    'aspirin': {'code': '161', 'display': 'Aspirin'},
    'diclofenac': {'code': '1066', 'display': 'Diclofenac'},

    # Antibiotics
    'amoxicillin': {'code': '71160', 'display': 'Amoxicillin'},
    'penicillin': {'code': '7980', 'display': 'Penicillin'},
    'ciprofloxacin': {'code': '1174', 'display': 'Ciprofloxacin'},
    'azithromycin': {'code': '73667', 'display': 'Azithromycin'},
    'doxycycline': {'code': '1450', 'display': 'Doxycycline'},
    'metronidazole': {'code': '83412', 'display': 'Metronidazole'},
    'cotrimoxazole': {'code': '916', 'display': 'Cotrimoxazole'},

    # Antihypertensives
    'lisinopril': {'code': '78280', 'display': 'Lisinopril'},
    'amlodipine': {'code': '76488', 'display': 'Amlodipine'},
    'atenolol': {'code': '77070', 'display': 'Atenolol'},
    'hydrochlorothiazide': {'code': '73046', 'display': 'Hydrochlorothiazide'},
    'losartan': {'code': '78987', 'display': 'Losartan'},

    # Antidiabetics
    'metformin': {'code': '83595', 'display': 'Metformin'},
    'insulin': {'code': '5856', 'display': 'Insulin'},
    'glibenclamide': {'code': '73117', 'display': 'Glibenclamide'},

    # Antimalarials
    'artemether_lumefantrine': {'code': '77068', 'display': 'Artemether and Lumefantrine'},
    'chloroquine': {'code': '890', 'display': 'Chloroquine'},
    'quinine': {'code': '83023', 'display': 'Quinine'},
    'artesunate': {'code': '77067', 'display': 'Artesunate'},

    # Antiretrovirals
    'nevirapine': {'code': '80586', 'display': 'Nevirapine'},
    'lamivudine': {'code': '78643', 'display': 'Lamivudine'},
    'zidovudine': {'code': '86663', 'display': 'Zidovudine'},
    'efavirenz': {'code': '75628', 'display': 'Efavirenz'},
    'tenofovir': {'code': '84309', 'display': 'Tenofovir'},

    # Respiratory
    'salbutamol': {'code': '83416', 'display': 'Salbutamol'},
    'prednisolone': {'code': '82924', 'display': 'Prednisolone'},

    # Gastrointestinal
    'omeprazole': {'code': '80945', 'display': 'Omeprazole'},
    'ranitidine': {'code': '83018', 'display': 'Ranitidine'},
    'oral_rehydration_salts': {'code': '80626', 'display': 'Oral rehydration salts'},

    # Vitamins & Supplements
    'folic_acid': {'code': '72829', 'display': 'Folic acid'},
    'iron': {'code': '77107', 'display': 'Iron'},
    'vitamin_b_complex': {'code': '86013', 'display': 'Vitamin B complex'},
    'multivitamin': {'code': '79346', 'display': 'Multivitamin'},
}

# ============================================================================
# COMMON ALLERGENS - CIEL Codes
# ============================================================================

CIEL_ALLERGIES = {
    # Medication Allergies
    'penicillin': {
        'code': '70875',
        'display': 'Penicillin',
        'category': 'medication',
    },
    'sulfa': {
        'code': '162299',
        'display': 'Sulfonamide',
        'category': 'medication',
    },
    'aspirin': {
        'code': '162297',
        'display': 'Aspirin',
        'category': 'medication',
    },
    'ibuprofen': {
        'code': '162298',
        'display': 'Ibuprofen',
        'category': 'medication',
    },

    # Food Allergies
    'peanuts': {
        'code': '162298',
        'display': 'Peanuts',
        'category': 'food',
    },
    'shellfish': {
        'code': '162302',
        'display': 'Shellfish',
        'category': 'food',
    },
    'eggs': {
        'code': '162300',
        'display': 'Eggs',
        'category': 'food',
    },
    'milk': {
        'code': '162301',
        'display': 'Milk',
        'category': 'food',
    },

    # Environmental Allergies
    'latex': {
        'code': '111088007',
        'display': 'Latex',
        'category': 'environment',
    },
    'pollen': {
        'code': '162303',
        'display': 'Pollen',
        'category': 'environment',
    },
    'dust': {
        'code': '162304',
        'display': 'Dust',
        'category': 'environment',
    },
}

# ============================================================================
# COMMON SYMPTOMS - CIEL Codes
# ============================================================================

CIEL_SYMPTOMS = {
    'headache': {
        'code': '139084',
        'display': 'Headache',
    },
    'dizziness': {
        'code': '141830',
        'display': 'Dizziness',
    },
    'chest_pain': {
        'code': '120749',
        'display': 'Chest pain',
    },
    'fatigue': {
        'code': '140501',
        'display': 'Fatigue',
    },
    'nausea': {
        'code': '5978',
        'display': 'Nausea',
    },
    'vomiting': {
        'code': '122983',
        'display': 'Vomiting',
    },
    'diarrhea': {
        'code': '142412',
        'display': 'Diarrhea',
    },
    'cough': {
        'code': '143264',
        'display': 'Cough',
    },
    'fever': {
        'code': '140238',
        'display': 'Fever',
    },
    'shortness_of_breath': {
        'code': '141600',
        'display': 'Shortness of breath',
    },
    'abdominal_pain': {
        'code': '151',
        'display': 'Abdominal pain',
    },
    'back_pain': {
        'code': '111487',
        'display': 'Back pain',
    },
    'joint_pain': {
        'code': '116558',
        'display': 'Joint pain',
    },
    'rash': {
        'code': '512',
        'display': 'Rash',
    },
    'sweating': {
        'code': '126952',
        'display': 'Sweating',
    },
    'loss_of_appetite': {
        'code': '134366',
        'display': 'Loss of appetite',
    },
    'weight_loss': {
        'code': '832',
        'display': 'Weight loss',
    },
}

# ============================================================================
# CLINICAL DECISION RECORD SYMPTOM MAPPING
# ============================================================================
# Maps ClinicalDecisionRecord boolean fields to CIEL symptom codes

CLINICAL_DECISION_SYMPTOM_MAPPING = {
    'headache': 'headache',
    'dizziness': 'dizziness',
    'blurred_vision': {
        'code': '114100',
        'display': 'Blurred vision',
    },
    'palpitations': {
        'code': '120749',
        'display': 'Palpitations',
    },
    'fatigue': 'fatigue',
    'chest_pain': 'chest_pain',
    'frequent_thirst': {
        'code': '5978',
        'display': 'Excessive thirst',
    },
    'loss_of_appetite': 'loss_of_appetite',
    'frequent_urination': {
        'code': '5953',
        'display': 'Frequent urination',
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_vital_sign_info(vital_type):
    """
    Get vital sign information including code, display name, and normal ranges.

    Args:
        vital_type (str): Key from CIEL_VITALS dict

    Returns:
        dict: Vital sign information or None if not found
    """
    return CIEL_VITALS.get(vital_type)


def get_condition_codes(condition_name):
    """
    Get both CIEL and ICD-10 codes for a condition.

    Args:
        condition_name (str): Key from CIEL_CONDITIONS dict

    Returns:
        dict: Condition information with both codes or None if not found
    """
    return CIEL_CONDITIONS.get(condition_name.lower().replace(' ', '_'))


def get_medication_code(medication_name):
    """
    Get CIEL code for a medication.

    Args:
        medication_name (str): Key from CIEL_MEDICATIONS dict

    Returns:
        dict: Medication information or None if not found
    """
    return CIEL_MEDICATIONS.get(medication_name.lower().replace(' ', '_'))


def get_allergy_info(allergen_name):
    """
    Get allergy information including code and category.

    Args:
        allergen_name (str): Key from CIEL_ALLERGIES dict

    Returns:
        dict: Allergy information or None if not found
    """
    return CIEL_ALLERGIES.get(allergen_name.lower().replace(' ', '_'))


def get_symptom_code(symptom_name):
    """
    Get CIEL code for a symptom.

    Args:
        symptom_name (str): Key from CIEL_SYMPTOMS dict

    Returns:
        dict: Symptom information or None if not found
    """
    return CIEL_SYMPTOMS.get(symptom_name.lower().replace(' ', '_'))


def search_condition_by_text(search_text):
    """
    Search for a condition by partial text match in display name.

    Args:
        search_text (str): Text to search for in condition names

    Returns:
        list: List of matching condition entries
    """
    search_lower = search_text.lower()
    matches = []

    for key, value in CIEL_CONDITIONS.items():
        if search_lower in value['display'].lower() or search_lower in key:
            matches.append({
                'key': key,
                'ciel': value['ciel'],
                'icd10': value['icd10'],
                'display': value['display'],
            })

    return matches


def search_medication_by_text(search_text):
    """
    Search for a medication by partial text match in display name.

    Args:
        search_text (str): Text to search for in medication names

    Returns:
        list: List of matching medication entries
    """
    search_lower = search_text.lower()
    matches = []

    for key, value in CIEL_MEDICATIONS.items():
        if search_lower in value['display'].lower() or search_lower in key:
            matches.append({
                'key': key,
                'code': value['code'],
                'display': value['display'],
            })

    return matches
