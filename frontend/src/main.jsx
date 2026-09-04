import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import App from './App.jsx';
import './index.css';

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const isClerkActive = Boolean(
  clerkPubKey && 
  clerkPubKey.trim() !== '' && 
  !clerkPubKey.includes('placeholder')
);

function Root() {
  if (!isClerkActive) {
    return (
      <React.StrictMode>
        <App isClerkConfigured={false} />
      </React.StrictMode>
    );
  }

  return (
    <React.StrictMode>
      <ClerkProvider publishableKey={clerkPubKey}>
        <App isClerkConfigured={true} />
      </ClerkProvider>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<Root />);
