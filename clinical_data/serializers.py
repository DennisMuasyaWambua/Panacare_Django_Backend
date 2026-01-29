"""
FHIR Serializers for clinical data resources

These serializers convert FHIR resource objects to JSON format for API responses.
They follow the existing pattern from fhir_api/serializers.py by delegating
serialization to the FHIR library's built-in as_json() method.
"""

from rest_framework import serializers


class FHIRSerializer(serializers.Serializer):
    """
    Base serializer for FHIR resources.
    Delegates JSON serialization to the FHIR resource's as_json() method.
    """

    def to_representation(self, instance):
        """
        Convert FHIR resource instance to JSON dictionary.

        Args:
            instance: FHIR resource object from fhir.resources library

        Returns:
            dict: JSON representation of the FHIR resource
        """
        if hasattr(instance, 'as_json'):
            return instance.as_json()
        return super().to_representation(instance)


class ObservationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Observation resources.
    Used for vitals, symptoms, and clinical observations.
    """

    class Meta:
        ref_name = 'FHIRObservation'


class ConditionFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Condition resources.
    Used for diagnoses and medical problems.
    """

    class Meta:
        ref_name = 'FHIRCondition'


class MedicationRequestFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR MedicationRequest resources.
    Used for prescriptions written by doctors.
    """

    class Meta:
        ref_name = 'FHIRMedicationRequest'


class MedicationStatementFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR MedicationStatement resources.
    Used for medication history (what patient is taking).
    """

    class Meta:
        ref_name = 'FHIRMedicationStatement'


class AllergyIntoleranceFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR AllergyIntolerance resources.
    Used for patient allergies and intolerances.
    """

    class Meta:
        ref_name = 'FHIRAllergyIntolerance'


class BundleSerializer(FHIRSerializer):
    """
    Serializer for FHIR Bundle resources.
    Used to wrap collections of resources in list responses.
    """

    class Meta:
        ref_name = 'FHIRBundle'


def create_bundle(resources, bundle_type="searchset"):
    """
    Create a FHIR Bundle containing multiple resources.

    Args:
        resources: List of FHIR resource objects
        bundle_type: Type of bundle (searchset, collection, transaction, etc.)

    Returns:
        Bundle: FHIR Bundle resource
    """
    from fhir.resources.bundle import Bundle, BundleEntry

    bundle = Bundle()
    bundle.type = bundle_type
    bundle.total = len(resources)

    entries = []
    for resource in resources:
        entry = BundleEntry()
        entry.resource = resource
        entry.fullUrl = f"urn:uuid:{resource.id}"
        entries.append(entry)

    bundle.entry = entries

    return bundle
