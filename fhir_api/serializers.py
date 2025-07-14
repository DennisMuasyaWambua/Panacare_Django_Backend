from rest_framework import serializers
import json
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.bundle import Bundle
from fhir.resources.fhirtypes import ResourceType


class FHIRSerializer(serializers.Serializer):
    """
    Base serializer for FHIR resources
    """
    def to_representation(self, instance):
        """
        Convert FHIR resource to JSON
        """
        # Use the resource's as_json() method to convert to JSON
        if hasattr(instance, 'as_json'):
            return instance.as_json()
        return super().to_representation(instance)


class PatientFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Patient resource
    """
    class Meta:
        model = FHIRPatient


class PractitionerFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Practitioner resource
    """
    class Meta:
        model = FHIRPractitioner


class OrganizationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Organization resource
    """
    class Meta:
        model = FHIROrganization


class EncounterFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Encounter resource
    """
    class Meta:
        model = FHIREncounter


class BundleSerializer(FHIRSerializer):
    """
    Serializer for FHIR Bundle resource
    """
    class Meta:
        model = Bundle


def create_bundle(resources, bundle_type="searchset"):
    """
    Create a FHIR Bundle containing multiple resources
    
    Args:
        resources: List of FHIR resources to include in the bundle
        bundle_type: Type of bundle (e.g. 'searchset', 'collection')
    
    Returns:
        A FHIR Bundle resource
    """
    entries = []
    
    for resource in resources:
        # Get the resource type (Patient, Practitioner, etc.)
        resource_type = resource.resource_type
        
        # Create an entry for this resource
        entry = {
            "fullUrl": f"{resource_type}/{resource.id}",
            "resource": resource,
        }
        
        entries.append(entry)
    
    # Create the bundle
    bundle = Bundle(
        type=bundle_type,
        entry=entries,
        total=len(entries)
    )
    
    return bundle