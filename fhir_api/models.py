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
>>>>>>> 36bf8daf6ce1d1522abcd52868ef039bde641224
import json

# This file won't define new models, it will serve as a bridge to convert 
# existing models to FHIR resources and vice versa
