import { initializeApp } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithCredential, signOut, onAuthStateChanged, setPersistence, browserLocalPersistence } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js";
import { Capacitor } from "@capacitor/core";
import { FirebaseAuthentication } from "@capacitor-firebase/authentication";

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
export const authReady = setPersistence(auth, browserLocalPersistence);
export const db = getFirestore(app);
export { onAuthStateChanged };

const provider = new GoogleAuthProvider();

export async function loginWithGoogle() {
  await authReady;

  // Android/iOS: use native Google Sign-In so the user returns to the app.
  // Web: retain the existing Firebase popup flow.
  if (Capacitor.isNativePlatform()) {
    const result = await FirebaseAuthentication.signInWithGoogle({
      skipNativeAuth: true
    });
    const idToken = result.credential?.idToken;
    if (!idToken) {
      throw new Error("Google Sign-In did not return an ID token. Check Firebase Android SHA-1 and Google provider settings.");
    }
    const credential = GoogleAuthProvider.credential(idToken);
    const webResult = await signInWithCredential(auth, credential);
    return webResult.user;
  }

  const result = await signInWithPopup(auth, provider);
  return result.user;
}

export async function logoutUser() {
  if (Capacitor.isNativePlatform()) {
    try { await FirebaseAuthentication.signOut(); } catch (_) {}
  }
  await signOut(auth);
}
