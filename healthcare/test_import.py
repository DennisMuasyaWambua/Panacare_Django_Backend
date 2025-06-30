from django.test import TestCase
from healthcare.models import Healthcare

class SimpleHealthcareImportTest(TestCase):
    def test_import_healthcare(self):
        # This test simply tries to import the Healthcare model
        # If it reaches here, the import was successful
        self.assertTrue(True)
