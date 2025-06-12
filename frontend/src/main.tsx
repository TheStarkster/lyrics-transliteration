import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://3ca670a0ce82c5f7ee1dd02a2fe77317@o376476.ingest.us.sentry.io/4509483876941824",
  sendDefaultPii: true
});



createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
