from rest_framework import serializers
import json
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.appointment import Appointment as FHIRAppointment
from fhir.resources.documentreference import DocumentReference as FHIRDocumentReference
from fhir.resources.diagnosticreport import DiagnosticReport as FHIRDiagnosticReport
from fhir.resources.procedure import Procedure as FHIRProcedure
from fhir.resources.careplan import CarePlan as FHIRCarePlan
from fhir.resources.careteam import CareTeam as FHIRCareTeam
from fhir.resources.task import Task as FHIRTask
from fhir.resources.communication import Communication as FHIRCommunication
from fhir.resources.medication import Medication as FHIRMedication
from fhir.resources.coverage import Coverage as FHIRCoverage
from fhir.resources.claim import Claim as FHIRClaim
from fhir.resources.consent import Consent as FHIRConsent
from fhir.resources.provenance import Provenance as FHIRProvenance
from fhir.resources.immunization import Immunization as FHIRImmunization
from fhir.resources.familymemberhistory import FamilyMemberHistory as FHIRFamilyMemberHistory
from fhir.resources.questionnaireresponse import QuestionnaireResponse as FHIRQuestionnaireResponse
from fhir.resources.specimen import Specimen as FHIRSpecimen
from fhir.resources.location import Location as FHIRLocation
from fhir.resources.device import Device as FHIRDevice
from fhir.resources.servicerequest import ServiceRequest as FHIRServiceRequest
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


class AppointmentFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Appointment resource
    """
    class Meta:
        model = FHIRAppointment


class DocumentReferenceFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR DocumentReference resource
    """
    class Meta:
        model = FHIRDocumentReference


class DiagnosticReportFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR DiagnosticReport resource
    """
    class Meta:
        model = FHIRDiagnosticReport


class ProcedureFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Procedure resource
    """
    class Meta:
        model = FHIRProcedure


class CarePlanFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR CarePlan resource
    """
    class Meta:
        model = FHIRCarePlan


class CareTeamFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR CareTeam resource
    """
    class Meta:
        model = FHIRCareTeam


class TaskFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Task resource
    """
    class Meta:
        model = FHIRTask


class CommunicationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Communication resource
    """
    class Meta:
        model = FHIRCommunication


class MedicationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Medication resource
    """
    class Meta:
        model = FHIRMedication


class CoverageFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Coverage resource
    """
    class Meta:
        model = FHIRCoverage


class ClaimFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Claim resource
    """
    class Meta:
        model = FHIRClaim


class ConsentFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Consent resource
    """
    class Meta:
        model = FHIRConsent


class ProvenanceFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Provenance resource
    """
    class Meta:
        model = FHIRProvenance


class ImmunizationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Immunization resource
    """
    class Meta:
        model = FHIRImmunization


class FamilyMemberHistoryFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR FamilyMemberHistory resource
    """
    class Meta:
        model = FHIRFamilyMemberHistory


class QuestionnaireResponseFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR QuestionnaireResponse resource
    """
    class Meta:
        model = FHIRQuestionnaireResponse


class SpecimenFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Specimen resource
    """
    class Meta:
        model = FHIRSpecimen


class LocationFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Location resource
    """
    class Meta:
        model = FHIRLocation


class DeviceFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR Device resource
    """
    class Meta:
        model = FHIRDevice


class ServiceRequestFHIRSerializer(FHIRSerializer):
    """
    Serializer for FHIR ServiceRequest resource
    """
    class Meta:
        model = FHIRServiceRequest


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