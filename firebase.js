import { initializeApp } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithCredential, signOut, onAuthStateChanged, setPersistence, browserLocalPersistence } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js";

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

// Do not statically import Capacitor packages here: this same file is loaded
// directly by GitHub Pages in an ordinary browser. Bare package imports would
// prevent the page module from starting before Firebase auth can initialize.
function isNativeCapacitorApp() {
  return !!(globalThis.Capacitor?.isNativePlatform?.() ||
    ["android", "ios"].includes(globalThis.Capacitor?.getPlatform?.()));
}

async function getNativeGoogleAuth() {
  const { FirebaseAuthentication } = await import("@capacitor-firebase/authentication");
  return FirebaseAuthentication;
}

export async function loginWithGoogle() {
  await authReady;

  if (isNativeCapacitorApp()) {
    const FirebaseAuthentication = await getNativeGoogleAuth();
    const result = await FirebaseAuthentication.signInWithGoogle({
      skipNativeAuth: true
    });
    const idToken = result.credential?.idToken;
    if (!idToken) {
      throw new Error("Google Sign-In did not return an ID token. Check Android OAuth client and signing certificate settings.");
    }
    const credential = GoogleAuthProvider.credential(idToken);
    const webResult = await signInWithCredential(auth, credential);
    return webResult.user;
  }

  const result = await signInWithPopup(auth, provider);
  return result.user;
}

export async function logoutUser() {
  if (isNativeCapacitorApp()) {
    try {
      const FirebaseAuthentication = await getNativeGoogleAuth();
      await FirebaseAuthentication.signOut();
    } catch (error) {
      console.warn("Native Google sign-out:", error);
    }
  }
  await signOut(auth);
}
