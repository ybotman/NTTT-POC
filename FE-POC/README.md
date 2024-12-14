# NameThatTangoTune

Project Overview
,
The “Name That Tango Tune” app is a React Native quiz game where users listen to tango song snippets and answer multiple-choice or free-form questions about the song’s title, orchestra, singer, and other attributes. The app will use Firebase for authentication, data storage, and audio hosting. A separate web-based admin app, built in React and hosted on Vercel, will allow administrators to manage quizzes and song metadata, including uploading audio snippets and defining quiz configurations. The app is designed for seamless scalability, using JSON-based data modeling for songs and quizzes.

Summary

“Name That Tango Tune” is a React/Next.js-based quiz app where users listen to tango song snippets and answer questions about the song’s title, orchestra, singer, and other attributes. The app leverages Firebase for authentication and data storage, Azure Blob Storage for hosting audio files, and Vercel for deployment. React audio libraries will be used for seamless playback, ensuring a smooth user experience.

Requirements
	1.	Frontend:
	•	Built with Next.js for SSR/CSR capabilities.
	•	React audio libraries (e.g., react-h5-audio-player or react-audio-player) for audio playback.
	•	Dynamic quiz pages with configurable questions (e.g., Song Title, Orchestra, Singer).
	•	User-friendly design with responsiveness.
	2.	Backend/Storage:
	•	Firebase Authentication for secure login (Google, email).
	•	Firebase Firestore for storing quiz metadata, user scores, and configurations.
	•	Azure Blob Storage for hosting and streaming audio files.
	•	CORS setup to allow audio access from Vercel-hosted apps.
	3.	Deployment:
	•	Deployed to Vercel for scalability, simplicity, and compatibility with Next.js.
	4.	Admin Features (Future):
	•	Admin app/dashboard to manage quizzes, upload songs, and configure metadata.

Decisions
	1.	Tech Stack:
	•	Frontend: React/Next.js for its flexibility and robust ecosystem.
	•	Backend: Firebase for real-time data management and authentication.
	•	Audio Storage: Azure Blob Storage for cost-effective and scalable hosting of audio files.
	•	Deployment: Vercel for its Next.js-first approach and automatic CI/CD pipeline.
	2.	Audio Handling:
	•	React audio libraries for cross-browser compatibility and ease of integration.
	•	Preloaded snippets streamed from Azure Blob Storage.
	3.	File Organization:
	•	Flat structure for Azure audio files; metadata stored in Firestore.
	•	JSON-based data models to define song metadata and quiz configurations.
	4.	User Experience:
	•	Focus on simple, intuitive interactions.
	•	Extendable for future features like leaderboards or advanced analytics.


Features and Requirements

User Quiz App
	1.	Authentication:
	•	Firebase Authentication for Google, email, or anonymous sign-ins.
	2.	Quiz Features:
	•	Users can select from a list of available quizzes.
	•	Quizzes are configurable, supporting:
	•	Multiple songs per quiz.
	•	Multiple question categories per song (e.g., Title, Orchestra, Singer).
	•	Time limits for answering each question.
	•	Real-time scoring based on user responses and category weights.
	3.	Song Playback:
	•	Play snippets of audio with start/stop times.
	4.	Results:
	•	Display a detailed score breakdown by category after quiz completion.

Admin App
	1.	Song Management:
	•	Upload and edit song audio snippets.
	•	Configure metadata:
	•	Title, Orchestra, Singer, Composer, Year, Style.
	•	Snippet start/stop times.
	2.	Quiz Management:
	•	Define quizzes with:
	•	Song lists.
	•	Question categories.
	•	Scoring rules and time limits.

Technology Stack

Frontend (User App and Admin App)
	•	React Native (User App):
	•	Framework for cross-platform (iOS/Android) development.
	•	Libraries:
	•	react-navigation for navigation.
	•	expo-av or react-native-sound for audio playback.
	•	@react-native-firebase/auth and firestore for Firebase integration.
	•	React (Admin App):
	•	Hosted on Vercel for scalability and ease of deployment.
	•	Libraries:
	•	Material-UI for a polished UI.
	•	Firebase Admin SDK for managing Firestore and storage.

Backend (Firebase)
	1.	Authentication:
	•	Firebase Authentication for managing user accounts.
	2.	Database:
	•	Firestore with a nested JSON model for songs and quizzes:
	•	Song example:

{
  "id": "song1",
  "title": "La Cumparsita",
  "year": 1935,
  "metadata": {
    "orchestra": "Juan D'Arienzo",
    "composer": "Gerardo Matos Rodríguez",
    "style": "Tango",
    "singer": {
      "name": "Alberto Echagüe",
      "obscurity_level": "low"
    }
  },
  "audio": {
    "url": "https://storage.googleapis.com/song1.mp3",
    "start_time": 15,
    "end_time": 25
  }
}


	•	Quiz example:

{
  "id": "quiz1",
  "name": "Simple Quiz",
  "description": "10 songs, 10-second questions.",
  "songs": ["song1", "song2", "song3"],
  "categories": ["Song Title", "Orchestra", "Singer"],
  "scoring": {
    "Song Title": 10,
    "Orchestra": 5,
    "Singer": 15
  },
  "time_limit": 10
}


	3.	Storage:
	•	Firebase Storage for hosting audio files and other media.

Hosting
	•	Vercel:
	•	Host the admin app for reliable, fast deployments.
