import { initializeApp } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, setPersistence, browserLocalPersistence } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.5.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyCO3hWdEOYF2-NhFp4mDtPtUqziYoQMbFM",
  authDomain: "kvk-voice-app.firebaseapp.com",
  projectId: "kvk-voice-app",
  storageBucket: "kvk-voice-app.firebasestorage.app",
  messagingSenderId: "232069395880",
  appId: "1:232069395880:web:4c3d527a1e2ed82b70d99d",
  measurementId: "G-R7051KZWTK"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
// Keep Google login active across refreshes and browser restarts.
export const authReady = setPersistence(auth, browserLocalPersistence);
export const db = getFirestore(app);
export { onAuthStateChanged };

const provider = new GoogleAuthProvider();

export async function loginWithGoogle() {
  await authReady;
  const result = await signInWithPopup(auth, provider);
  return result.user;
}

export async function logoutUser() {
  await signOut(auth);
}
