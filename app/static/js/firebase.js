// Fixed & Cleaned Firebase Auth + Streak Tracking Code

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import { getFirestore, setDoc, doc, getDoc, updateDoc } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyCLtZwe2I1CJZUS4q5hcQXwUfFfbxNIirQ",
  authDomain: "heartguard-f00a0.firebaseapp.com",
  projectId: "heartguard-f00a0",
  storageBucket: "heartguard-f00a0.firebasestorage.app",
  messagingSenderId: "419587768914",
  appId: "1:419587768914:web:c63d6675de87c491a0d58b"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth();
const db = getFirestore();

function showMessage(message, divId) {
  const messageDiv = document.getElementById(divId);
  messageDiv.style.display = "block";
  messageDiv.innerHTML = message;
  messageDiv.style.opacity = 1;
  setTimeout(() => {
    messageDiv.style.opacity = 0;
  }, 5000);
}

// Sign Up
const signUp = document.getElementById('submitSignUp');
signUp.addEventListener('click', async (event) => {
  event.preventDefault();
  console.log("Sign up button clicked"); // Debug log

  const email = document.getElementById('rEmail').value;
  const password = document.getElementById('rPassword').value;
  const firstName = document.getElementById('fName').value;
  const lastName = document.getElementById('lName').value;

    // Add validation
    if (!email || !password || !firstName || !lastName) {
        showMessage('Please fill all fields', 'signUpMessage');
        return;
      }

  try {
    console.log("Attempting to create user..."); // Debug log
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    const todayStr = new Date().toISOString().split('T')[0];
    console.log("User created:", user.uid); // Debug log

    const userData = {
      email,
      firstName,
      lastName,
      lastLoginDate: todayStr,
      streak: 1
    };

    await setDoc(doc(db, "users", user.uid), userData);
    console.log("User data saved to Firestore"); // Debug log
    showMessage('Account Created Successfully', 'signUpMessage');
    window.location.href = '/';

  } catch (error) {
    console.error("Signup error:", error); // Debug log
    if (error.code === 'auth/email-already-in-use') {
      showMessage('Email Address Already Exists !!!', 'signUpMessage');
    } else if (error.code === 'auth/weak-password') {
        showMessage('Password should be at least 6 characters', 'signUpMessage');
    } else {
      showMessage('Unable to create user', 'signUpMessage');
    }
  }
});

// Sign In
const signIn = document.getElementById('submitSignIn');
signIn.addEventListener('click', async (event) => {
  event.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  console.log("Attempting login with:", email); // Debug log

  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    console.log("Firebase auth success, user:", user.uid); // debug log

     // Send token to your backend for session creation
    const token = await user.getIdToken();

    console.log("Firebase ID token:", token); // Verify token is generated

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
    });
    
    const data = await response.json();
    console.log("Backend response:", data); // Debug response

    if (response.ok) {
        window.location.href = '/';  // Redirect to home
    } else {
        showMessage('Login failed: '+ (data.error || 'Unknown error'), 'signInMessage');
    }

  } catch (error) {
    if (error.code === 'auth/invalid-credential') {
      showMessage('Incorrect Email or Password', 'signInMessage');
    } else {
      showMessage('Account does not Exist', 'signInMessage');
    }
  }
});

// Helper function for Firebase errors
function getFirebaseError(error) {
  switch(error.code) {
    case 'auth/invalid-email': return 'Invalid email address';
    case 'auth/user-disabled': return 'Account disabled';
    case 'auth/user-not-found': return 'Account not found';
    case 'auth/wrong-password': return 'Incorrect password';
    default: return 'Login failed. Please try again.';
  }
}