<<<<<<< HEAD
# from django.db import models
# from fhir.resources.patient import Patient as FHIRPatient
# from fhir.resources.practitioner import Practitioner as FHIRPractitioner
# from fhir.resources.organization import Organization as FHIROrganization
# from fhir.resources.encounter import Encounter as FHIREncounter
# from fhir.resources.schedule import Schedule
# from fhir.resources.appointment import Appointment
# import uuid
=======
from django.db import models
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.schedule import Schedule
from fhir.resources.appointment import Appointment
import uuid
>>>>>>> f2378c294f620e0fd07f542bd66d7b2ff9075d71
import json

# This file won't define new models, it will serve as a bridge to convert 
# existing models to FHIR resources and vice versa
