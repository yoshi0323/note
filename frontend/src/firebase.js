// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDU7l4iKUz4VGVePD7uufmlJDfV_AyFgqI",
  authDomain: "note-c801b.firebaseapp.com",
  projectId: "note-c801b",
  storageBucket: "note-c801b.firebasestorage.app",
  messagingSenderId: "449008432413",
  appId: "1:449008432413:web:11a7f0d0f7faa63e231df4",
  measurementId: "G-88W2S594MT"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Analytics (only in production)
let analytics = null;
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  analytics = getAnalytics(app);
}

export { app, analytics };

