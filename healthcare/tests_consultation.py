from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Role, Patient
from doctors.models import Doctor
from healthcare.models import Healthcare, Appointment, Consultation, ConsultationChat
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone

User = get_user_model()

class ConsultationTests(TestCase):
    def setUp(self):
        # Create roles using get_or_create to avoid duplicates
        self.admin_role, _ = Role.objects.get_or_create(name='admin')
        self.doctor_role, _ = Role.objects.get_or_create(name='doctor')
        self.patient_role, _ = Role.objects.get_or_create(name='patient')

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        self.admin_user.roles.add(self.admin_role)

        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@example.com',
            password='password123'
        )
        self.doctor_user.roles.add(self.doctor_role)
        
        # Create healthcare facility
        self.healthcare = Healthcare.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone_number='1234567890'
        )
        
        # Create education first (required for doctor)
        from doctors.models import Education
        self.education, _ = Education.objects.get_or_create(
            level_of_education='MD',
            field='Medicine',
            institution='Test University'
        )
        
        # Create doctor
        self.doctor, _ = Doctor.objects.get_or_create(
            user=self.doctor_user,
            defaults={
                'specialty': 'General',
                'bio': 'Test bio',
                'license_number': 'LIC123456',
                'education': self.education,
                'facility_name': self.healthcare.name
            }
        )
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='password123'
        )
        self.patient_user.roles.add(self.patient_role)
        
        # Create patient
        self.patient, _ = Patient.objects.get_or_create(
            user=self.patient_user,
            defaults={
                'date_of_birth': date(1990, 1, 1),
                'gender': 'male',
                # phone='0987654321', # Removed as it's not a required field in Patient model
                # address='456 Patient St' # Removed as it's not a required field in Patient model
            }
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            healthcare_facility=self.healthcare,
            appointment_date=date.today() + timedelta(days=1),
            start_time='10:00:00',
            end_time='10:30:00',
            status='scheduled',
            appointment_type='consultation'
        )
        
        # Create consultation
        self.consultation = Consultation.objects.create(
            appointment=self.appointment,
            status='scheduled'
        )
        
        # Set up API client
        self.client = APIClient()

    @patch('healthcare.views.create_twilio_room')
    @patch('healthcare.views.generate_twilio_token')
    def test_start_consultation(self, mock_generate_token, mock_create_room):
        """
        Test starting a consultation with Twilio integration
        """
        # Mock Twilio responses
        mock_room = MagicMock()
        mock_room.sid = 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        mock_create_room.return_value = mock_room
        
        # Mock token generation
        mock_generate_token.return_value = 'mock-twilio-token'
        
        # Authenticate as doctor
        self.client.force_authenticate(user=self.doctor_user)
        
        # Start consultation
        url = reverse('consultation-start-consultation', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in-progress')
        self.assertIsNotNone(response.data['twilio_room_name'])
        self.assertIn('token', response.data)
        
        # Verify consultation was updated in DB
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, 'in-progress')
        self.assertEqual(self.consultation.twilio_room_sid, 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        self.assertIsNotNone(self.consultation.doctor_token)
        self.assertIsNotNone(self.consultation.patient_token)
        
        # Verify token generation calls
        self.assertEqual(mock_generate_token.call_count, 2)  # One for doctor, one for patient

    @patch('healthcare.views.close_twilio_room')
    def test_end_consultation(self, mock_close_room):
        """
        Test ending a consultation with Twilio integration
        """
        # Set up in-progress consultation with Twilio room
        self.consultation.status = 'in-progress'
        self.consultation.start_time = timezone.now()
        self.consultation.twilio_room_sid = 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        self.consultation.save()
        
        # Authenticate as doctor
        self.client.force_authenticate(user=self.doctor_user)
        
        # End consultation
        url = reverse('consultation-end-consultation', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify consultation was updated in DB
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, 'completed')
        self.assertIsNotNone(self.consultation.end_time)
        
        # Verify Twilio room was closed
        mock_close_room.assert_called_once_with('RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

    @patch('healthcare.views.generate_twilio_token')
    def test_get_token(self, mock_generate_token):
        """
        Test getting a Twilio token for a consultation
        """
        # Mock token generation
        mock_generate_token.return_value = 'new-mock-token'
        
        # Set up in-progress consultation with Twilio room
        self.consultation.status = 'in-progress'
        self.consultation.twilio_room_name = 'test-room'
        self.consultation.doctor_token = 'doctor-token'
        self.consultation.patient_token = 'patient-token'
        self.consultation.save()
        
        # Authenticate as patient
        self.client.force_authenticate(user=self.patient_user)
        
        # Get token
        url = reverse('consultation-get-token', kwargs={'pk': self.consultation.id})
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'patient-token')
        self.assertEqual(response.data['room_name'], 'test-room')
        
        # Should not have generated a new token since one exists
        mock_generate_token.assert_not_called()
        
        # Test with missing token
        self.consultation.patient_token = ''
        self.consultation.save()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'new-mock-token')
        
        # Should have generated a new token
        mock_generate_token.assert_called_once()

    @patch('healthcare.views.generate_twilio_token')
    def test_join_consultation(self, mock_generate_token):
        """
        Test joining an ongoing consultation
        """
        # Mock token generation
        mock_generate_token.return_value = 'new-join-token'

        # Set up in-progress consultation with Twilio room
        self.consultation.status = 'in-progress'
        self.consultation.twilio_room_name = 'join-test-room'
        self.consultation.doctor_token = 'doctor-join-token'
        self.consultation.patient_token = 'patient-join-token'
        self.consultation.save()

        # Authenticate as patient and join
        self.client.force_authenticate(user=self.patient_user)
        url = reverse('consultation-join-consultation', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'patient-join-token')
        self.assertEqual(response.data['room_name'], 'join-test-room')
        mock_generate_token.assert_not_called() # Token already exists

        # Test with missing patient token
        self.consultation.patient_token = ''
        self.consultation.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'new-join-token')
        mock_generate_token.assert_called_once() # New token generated

        # Authenticate as doctor and join
        mock_generate_token.reset_mock() # Reset mock for doctor test
        self.client.force_authenticate(user=self.doctor_user)
        self.consultation.doctor_token = '' # Clear doctor token for new generation
        self.consultation.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'new-join-token')
        mock_generate_token.assert_called_once() # New token generated

    def test_send_message(self):
        """
        Test sending chat messages in a consultation
        """
        self.consultation.status = 'in-progress'
        self.consultation.save()

        # Authenticate as doctor and send message
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse('consultation-send-message', kwargs={'pk': self.consultation.id})
        response = self.client.post(url, {'message': 'Hello from doctor!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Hello from doctor!')
        self.assertTrue(response.data['is_doctor'])
        self.assertEqual(ConsultationChat.objects.count(), 1)

        # Authenticate as patient and send message
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(url, {'message': 'Hi from patient!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Hi from patient!')
        self.assertFalse(response.data['is_doctor'])
        self.assertEqual(ConsultationChat.objects.count(), 2)

        # Test sending empty message
        response = self.client.post(url, {'message': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Message content is required', response.data['error'])

        # Test sending message when consultation is not in-progress
        self.consultation.status = 'completed'
        self.consultation.save()
        response = self.client.post(url, {'message': 'Should not send'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot send messages in a consultation with status: completed', response.data['error'])

    def test_chat_messages(self):
        """
        Test retrieving chat messages for a consultation
        """
        self.consultation.status = 'in-progress'
        self.consultation.save()

        # Send some messages
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.doctor_user, message='Doc message 1', is_doctor=True)
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.patient_user, message='Patient message 1', is_doctor=False)
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.doctor_user, message='Doc message 2', is_doctor=True)

        # Authenticate as doctor and retrieve messages
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse('consultation-chat-messages', kwargs={'pk': self.consultation.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['message'], 'Doc message 2') # Ordered by newest first

        # Authenticate as patient and retrieve messages
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['message'], 'Doc message 2')

        # Test with limit
        response = self.client.get(url + '?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], 'Doc message 2')

    def test_mark_messages_read(self):
        """
        Test marking messages as read
        """
        self.consultation.status = 'in-progress'
        self.consultation.save()

        # Doctor sends messages
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.doctor_user, message='Doc message 1', is_doctor=True, is_read=False)
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.doctor_user, message='Doc message 2', is_doctor=True, is_read=False)
        # Patient sends messages
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.patient_user, message='Patient message 1', is_doctor=False, is_read=False)
        ConsultationChat.objects.create(consultation=self.consultation, sender=self.patient_user, message='Patient message 2', is_doctor=False, is_read=False)

        # Authenticate as patient and mark doctor's messages as read
        self.client.force_authenticate(user=self.patient_user)
        url = reverse('consultation-mark-messages-read', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['messages_marked_read'], 2)
        self.assertEqual(ConsultationChat.objects.filter(is_doctor=True, is_read=True).count(), 2)
        self.assertEqual(ConsultationChat.objects.filter(is_doctor=False, is_read=False).count(), 2) # Patient's messages should still be unread

        # Authenticate as doctor and mark patient's messages as read
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['messages_marked_read'], 2)
        self.assertEqual(ConsultationChat.objects.filter(is_doctor=False, is_read=True).count(), 2)
        self.assertEqual(ConsultationChat.objects.filter(is_doctor=True, is_read=True).count(), 2) # Doctor's messages should remain read
