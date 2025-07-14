# Twilio Video Integration for Consultations

This document explains how to set up and use the Twilio Video integration for doctor-patient consultations.

## Setup

1. **Requirements**:
   - Twilio account with Video API access
   - Python package: `twilio`

2. **Environment Variables**:

   Add these to your environment or .env file:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_API_KEY_SID=your_api_key_sid
   TWILIO_API_KEY_SECRET=your_api_key_secret
   ```

3. **Obtaining Twilio Credentials**:
   - Create a Twilio account at https://www.twilio.com
   - Navigate to the Video Console
   - Create an API Key and Secret (store these securely)
   - Copy your Account SID and Auth Token from the dashboard

## API Endpoints

### Doctor Endpoints

1. **Start Consultation**:
   - URL: `POST /api/consultations/{id}/start_consultation/`
   - Description: Starts a video consultation and creates a Twilio room
   - Authentication: Doctor only
   - Response: Consultation details with Twilio token for the doctor

2. **End Consultation**:
   - URL: `POST /api/consultations/{id}/end_consultation/`
   - Description: Ends the video consultation and closes the Twilio room
   - Authentication: Doctor only
   - Response: Updated consultation details

### Patient/Doctor Endpoints

1. **Get Token**:
   - URL: `GET /api/consultations/{id}/get_token/`
   - Description: Retrieves the Twilio token for joining the consultation
   - Authentication: Patient or Doctor associated with the consultation
   - Response: Twilio token and room name

2. **Join Consultation** (primarily for patients):
   - URL: `POST /api/consultations/{id}/join_consultation/`
   - Description: Endpoint for patients to join a consultation
   - Authentication: Patient associated with the consultation
   - Response: Twilio token and room name

## Frontend Implementation Guide

To implement video consultations in your frontend:

1. **Install Twilio Video JS SDK**:
   ```
   npm install twilio-video
   ```

2. **Connect to a Room**:
   ```javascript
   import Video from 'twilio-video';

   async function joinVideoCall(token, roomName) {
     try {
       // Connect to the Room with the token
       const room = await Video.connect(token, {
         name: roomName,
         audio: true,
         video: true
       });

       // Handle connected participant (local participant)
       handleLocalParticipant(room.localParticipant);

       // Handle already connected participants
       room.participants.forEach(participant => {
         handleRemoteParticipant(participant);
       });

       // Handle participants connecting
       room.on('participantConnected', participant => {
         handleRemoteParticipant(participant);
       });

       // Handle participants disconnecting
       room.on('participantDisconnected', participant => {
         console.log(`Participant ${participant.identity} disconnected`);
         // Remove participant from the UI
       });

       // Return the room so it can be used later
       return room;
     } catch (error) {
       console.error(`Error connecting to the room: ${error.message}`);
     }
   }

   function handleLocalParticipant(participant) {
     // Attach local video to the UI
     participant.tracks.forEach(publication => {
       if (publication.track) {
         attachTrackToUI(publication.track, 'local-media-container');
       }
     });

     // Handle new track publications
     participant.on('trackPublished', publication => {
       if (publication.track) {
         attachTrackToUI(publication.track, 'local-media-container');
       }
     });
   }

   function handleRemoteParticipant(participant) {
     console.log(`Participant ${participant.identity} connected`);

     // Create a container for this participant
     const participantContainer = document.createElement('div');
     participantContainer.id = participant.identity;
     document.getElementById('remote-media-container').appendChild(participantContainer);

     // Attach existing tracks
     participant.tracks.forEach(publication => {
       if (publication.isSubscribed) {
         attachTrackToUI(publication.track, participant.identity);
       }
     });

     // Handle subscribed tracks
     participant.on('trackSubscribed', track => {
       attachTrackToUI(track, participant.identity);
     });

     // Handle unsubscribed tracks
     participant.on('trackUnsubscribed', track => {
       track.detach().forEach(element => element.remove());
     });
   }

   function attachTrackToUI(track, containerId) {
     const container = document.getElementById(containerId);
     if (container && track) {
       track.attach().forEach(element => {
         container.appendChild(element);
       });
     }
   }
   ```

3. **Usage Flow**:

   **For Doctors**:
   - When starting a consultation, call the `/start_consultation/` endpoint
   - Use the returned token to connect to the Twilio room
   - When ending the consultation, call the `/end_consultation/` endpoint

   **For Patients**:
   - When joining a consultation, call the `/join_consultation/` endpoint
   - Use the returned token to connect to the Twilio room

4. **Disconnect from a Room**:
   ```javascript
   function leaveRoom(room) {
     if (room) {
       room.disconnect();
       console.log('Disconnected from the room');
     }
   }
   ```

## Testing

To test the integration:

1. Create two test users (doctor and patient)
2. Create an appointment and consultation
3. Have the doctor start the consultation
4. Have the patient join the consultation
5. Verify both can see and hear each other

## Troubleshooting

Common issues:

1. **Connection errors**: Check that your Twilio credentials are correct
2. **Permission errors**: Ensure the browser has permission to access camera and microphone
3. **No video/audio**: Check that the tracks are being published correctly

For more information, refer to the [Twilio Video documentation](https://www.twilio.com/docs/video).