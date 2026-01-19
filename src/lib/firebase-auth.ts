// Firebase Authentication utilities
import { auth } from './firebase';
import { 
  signInWithPopup, 
  GoogleAuthProvider, 
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser
} from 'firebase/auth';

// Whitelist of allowed admin emails
export const ALLOWED_ADMIN_EMAILS = [
  "rndpig@gmail.com",
  "annadilger@gmail.com",
  "bday1951@gmail.com",
  "drdcreek@gmail.com",
  "ericlday@gmail.com",
  "amyannday@gmail.com",
];

// Check if user email is in whitelist
export function isAllowedUser(user: FirebaseUser | null): boolean {
  if (!user?.email) return false;
  return ALLOWED_ADMIN_EMAILS.includes(user.email);
}

// Sign in with Google
export async function signInWithGoogle() {
  const provider = new GoogleAuthProvider();
  try {
    const result = await signInWithPopup(auth, provider);
    
    // Check if user is in whitelist
    if (!isAllowedUser(result.user)) {
      await firebaseSignOut(auth);
      throw new Error('Your email is not authorized to access this application.');
    }
    
    return result.user;
  } catch (error: any) {
    console.error('Sign in error:', error);
    throw error;
  }
}

// Sign out
export async function signOut() {
  try {
    await firebaseSignOut(auth);
  } catch (error) {
    console.error('Sign out error:', error);
    throw error;
  }
}

// Subscribe to auth state changes
export function onAuthStateChange(callback: (user: FirebaseUser | null) => void) {
  return onAuthStateChanged(auth, (user) => {
    // Only call callback with user if they're in whitelist
    if (user && !isAllowedUser(user)) {
      firebaseSignOut(auth);
      callback(null);
    } else {
      callback(user);
    }
  });
}
