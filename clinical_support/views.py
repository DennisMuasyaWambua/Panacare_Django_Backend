from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    ClinicalDecisionInputSerializer,
    ClinicalDecisionRecordSerializer,
    ClinicalDecisionResponseSerializer
)
from .models import ClinicalDecisionRecord
from users.models import Patient
from django.db.models import Q

class ClinicalDecisionSupportAPIView(APIView):
    """
    API view for clinical decision support
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        """Process clinical data and provide decision support"""
        serializer = ClinicalDecisionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the validated data
        validated_data = serializer.validated_data
        
        # Get the patient if available
        patient = None
        if hasattr(request.user, 'patient'):
            patient = request.user.patient
        
        # Create a record for the clinical decision
        record_data = dict(validated_data)
        record = ClinicalDecisionRecord.objects.create(
            patient=patient,
            **record_data
        )
        
        # Generate the analysis and recommendations
        analysis, recommendations, risk_level = self._analyze_clinical_data(validated_data)
        
        # Update the record with the analysis
        record.analysis = analysis
        record.recommendations = "\n".join(recommendations)
        record.risk_level = risk_level
        record.save()
        
        # Prepare the response
        # Get blood pressure and sugar status from the analysis function
        bp_status = None
        sugar_status = None
        
        if validated_data.get('systolic_pressure') and validated_data.get('diastolic_pressure'):
            # Check blood pressure status based on the same logic as in _analyze_clinical_data
            systolic = validated_data.get('systolic_pressure')
            diastolic = validated_data.get('diastolic_pressure')
            
            if systolic >= 180 or diastolic >= 120:
                bp_status = "too high"
            elif systolic >= 140 or diastolic >= 90:
                bp_status = "high"
            elif 120 <= systolic < 140 or 80 <= diastolic < 90:
                bp_status = "borderline high"
            elif systolic < 90 and diastolic < 60:
                bp_status = "too low"
            elif systolic < 100 and diastolic < 65:
                bp_status = "borderline low"
            else:
                bp_status = "normal"
        
        if validated_data.get('blood_sugar'):
            # Check blood sugar status based on the same logic as in _analyze_clinical_data
            blood_sugar = validated_data.get('blood_sugar')
            
            if blood_sugar >= 200:
                sugar_status = "too high"
            elif blood_sugar >= 126:
                sugar_status = "high"
            elif 100 <= blood_sugar < 126:
                sugar_status = "borderline high"
            elif blood_sugar < 70:
                sugar_status = "too low"
            elif 70 <= blood_sugar < 80:
                sugar_status = "borderline low"
            else:
                sugar_status = "normal"
        
        response_data = {
            'analysis': analysis,
            'recommendations': recommendations,
            'risk_level': risk_level,
            'record_id': record.id,
            'blood_pressure_status': bp_status,
            'blood_sugar_status': sugar_status
        }
        
        response_serializer = ClinicalDecisionResponseSerializer(data=response_data)
        if response_serializer.is_valid():
            return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _analyze_clinical_data(self, data):
        """
        Analyze the clinical data and return analysis, recommendations, and risk level
        """
        # Initialize variables
        analysis = ""
        recommendations = []
        risk_factors = []
        risk_level = "low"  # Default risk level
        
        # Extract values for easier access
        age = data.get('age')
        gender = data.get('gender')
        weight = data.get('weight')
        height = data.get('height')
        high_blood_pressure = data.get('high_blood_pressure', False)
        diabetes = data.get('diabetes', False)
        on_medication = data.get('on_medication', False)
        
        # Calculate BMI
        bmi = weight / ((height / 100) ** 2)
        bmi_category = ""
        if bmi < 18.5:
            bmi_category = "underweight"
        elif 18.5 <= bmi < 25:
            bmi_category = "normal weight"
        elif 25 <= bmi < 30:
            bmi_category = "overweight"
        else:
            bmi_category = "obese"
            risk_factors.append("obesity")
        
        # Check vitals
        systolic = data.get('systolic_pressure')
        diastolic = data.get('diastolic_pressure')
        blood_sugar = data.get('blood_sugar')
        heart_rate = data.get('heart_rate')
        
        # Blood pressure analysis
        bp_status = "normal"
        if systolic and diastolic:
            if systolic >= 180 or diastolic >= 120:
                bp_status = "too high"
                risk_factors.append("critically high blood pressure")
            elif systolic >= 140 or diastolic >= 90:
                bp_status = "high"
                risk_factors.append("high blood pressure")
            elif 120 <= systolic < 140 or 80 <= diastolic < 90:
                bp_status = "borderline high"
                risk_factors.append("elevated blood pressure")
            elif systolic < 90 and diastolic < 60:
                bp_status = "too low"
                risk_factors.append("low blood pressure")
            elif systolic < 100 and diastolic < 65:
                bp_status = "borderline low"
                risk_factors.append("somewhat low blood pressure")
        
        # Blood sugar analysis
        sugar_status = "normal"
        if blood_sugar:
            if blood_sugar >= 200:  # Severely high
                sugar_status = "too high"
                risk_factors.append("critically high blood sugar")
            elif blood_sugar >= 126:  # Fasting blood sugar >= 126 mg/dL indicates diabetes
                sugar_status = "high"
                risk_factors.append("high blood sugar")
            elif 100 <= blood_sugar < 126:
                sugar_status = "borderline high"
                risk_factors.append("pre-diabetic blood sugar levels")
            elif blood_sugar < 70:
                sugar_status = "too low"
                risk_factors.append("hypoglycemia")
            elif 70 <= blood_sugar < 80:
                sugar_status = "borderline low"
                risk_factors.append("somewhat low blood sugar")
        
        # Heart rate analysis
        heart_status = "normal"
        if heart_rate:
            if heart_rate > 100:
                heart_status = "elevated"
                risk_factors.append("elevated heart rate")
            elif heart_rate < 60:
                heart_status = "low"
                risk_factors.append("low heart rate")
        
        # Check existing conditions
        if high_blood_pressure:
            risk_factors.append("history of high blood pressure")
        
        if diabetes:
            risk_factors.append("history of diabetes")
        
        # Lifestyle factors
        if data.get('smokes', False):
            risk_factors.append("smoking")
        
        if data.get('consumes_alcohol', False):
            risk_factors.append("alcohol consumption")
        
        if data.get('eats_unhealthy', False):
            risk_factors.append("unhealthy diet")
        
        if data.get('skips_medication', False) and on_medication:
            risk_factors.append("medication non-compliance")
        
        # Exercise and sleep
        exercise_minutes = data.get('exercise_minutes')
        if exercise_minutes is not None and exercise_minutes < 30:
            risk_factors.append("insufficient exercise")
        
        sleep_hours = data.get('sleep_hours')
        if sleep_hours is not None and (sleep_hours < 7 or sleep_hours > 9):
            risk_factors.append("irregular sleep pattern")
        
        # Symptom analysis
        symptoms = []
        for symptom in [
            'headache', 'dizziness', 'blurred_vision', 'palpitations', 'fatigue', 
            'chest_pain', 'frequent_thirst', 'loss_of_appetite', 'frequent_urination'
        ]:
            if data.get(symptom, False):
                symptoms.append(symptom.replace('_', ' '))
        
        if data.get('other_symptoms'):
            symptoms.append(f"other symptoms: {data.get('other_symptoms')}")
        
        # Determine risk level based on factors
        if len(risk_factors) >= 3 or 'chest_pain' in symptoms:
            risk_level = "high"
        elif len(risk_factors) >= 1:
            risk_level = "moderate"
        
        # Generate analysis text
        analysis = f"You are a {age}-year-old {gender} with a BMI of {bmi:.1f} ({bmi_category}). "
        
        if high_blood_pressure or diabetes:
            conditions = []
            if high_blood_pressure:
                conditions.append("high blood pressure")
            if diabetes:
                conditions.append("diabetes")
            analysis += f"Your medical history includes {' and '.join(conditions)}. "
        
        if on_medication:
            analysis += "You are currently on medication. "
        
        if symptoms:
            analysis += f"You are presenting with the following symptoms: {', '.join(symptoms)}. "
        
        if systolic and diastolic:
            analysis += f"Your blood pressure is {systolic}/{diastolic} mmHg ({bp_status}). "
        
        if blood_sugar:
            analysis += f"Your blood sugar level is {blood_sugar} mg/dL ({sugar_status}). "
        
        if heart_rate:
            analysis += f"Your heart rate is {heart_rate} BPM ({heart_status}). "
        
        if risk_factors:
            analysis += f"Your risk factors include: {', '.join(risk_factors)}."
        
        # Generate recommendations
        if bmi_category in ["overweight", "obese"]:
            recommendations.append("Consider a balanced diet and regular exercise to achieve a healthy weight.")
        
        if bp_status in ["elevated", "high"] or high_blood_pressure:
            recommendations.append("Monitor blood pressure regularly and follow a low-sodium diet.")
            if bp_status == "high" and not on_medication:
                recommendations.append("Consult with a healthcare provider about medication options for blood pressure management.")
        
        if sugar_status in ["pre-diabetic", "high"] or diabetes:
            recommendations.append("Monitor blood sugar levels regularly and limit sugar intake.")
            if sugar_status == "high" and not on_medication:
                recommendations.append("Consult with a healthcare provider about diabetes management options.")
        
        if data.get('smokes', False):
            recommendations.append("Quitting smoking can significantly improve overall health. Consider smoking cessation programs.")
        
        if data.get('consumes_alcohol', False):
            recommendations.append("Limit alcohol consumption to improve overall health.")
        
        if data.get('eats_unhealthy', False):
            recommendations.append("Adopt a balanced diet rich in fruits, vegetables, and whole grains, while limiting processed foods.")
        
        if data.get('skips_medication', False) and on_medication:
            recommendations.append("Regularly taking prescribed medications is crucial for managing your condition effectively.")
        
        if exercise_minutes is None or exercise_minutes < 30:
            recommendations.append("Aim for at least 30 minutes of moderate exercise most days of the week.")
        
        if sleep_hours is None or sleep_hours < 7 or sleep_hours > 9:
            recommendations.append("Try to maintain a regular sleep schedule with 7-9 hours of sleep per night.")
        
        # General recommendations
        if 'chest_pain' in symptoms:
            recommendations.insert(0, "Chest pain can be a sign of a serious condition. Seek immediate medical attention.")
        
        if risk_level == "high":
            recommendations.insert(0, "Based on your risk factors, we recommend scheduling an appointment with a healthcare provider soon.")
        
        if not recommendations:
            recommendations.append("Continue with healthy lifestyle habits and regular check-ups.")
        
        return analysis, recommendations, risk_level


class PatientClinicalHistoryAPIView(APIView):
    """
    API view for retrieving a patient's clinical decision history
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """Get the clinical decision history for the authenticated patient"""
        # Ensure the user is a patient
        if not hasattr(request.user, 'patient'):
            return Response(
                {"detail": "Only patients can access their clinical history."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the patient's clinical decision records
        records = ClinicalDecisionRecord.objects.filter(
            patient=request.user.patient
        ).order_by('-created_at')
        
        # Serialize the records
        serializer = ClinicalDecisionRecordSerializer(records, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
