import React from 'react';
import { Link } from 'react-router-dom';

const TermsOfService: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-800">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Home
          </Link>
        </div>
        
        <div className="bg-white p-8 rounded-xl shadow-md">
          <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>
          
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. Introduction</h2>
            <p className="mb-4">
              Welcome to DestinPQ's Lyrics Transliteration Service. These Terms of Service govern your use of our application, website, and services provided by DESTINPQ LLP.
            </p>
            <p>
              By accessing or using our services, you agree to be bound by these Terms. If you disagree with any part of the terms, you may not access or use our services.
            </p>
          </section>
          
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. Use of Services</h2>
            <p className="mb-4">
              Our Lyrics Transliteration Service allows you to upload audio files to extract, transcribe, and transliterate lyrics with accurate timestamps. The service is provided for personal and commercial use, subject to these Terms.
            </p>
            <p>
              You are responsible for maintaining the confidentiality of your account and for restricting access to your computer or device. You agree to accept responsibility for all activities that occur under your account.
            </p>
          </section>
          
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. User Content</h2>
            <p className="mb-4">
              When you upload content to our service, you retain ownership of your intellectual property rights. However, by uploading content, you grant DestinPQ a limited license to use, store, and process that content for the purpose of providing our services.
            </p>
            <p>
              You represent and warrant that you own or have the necessary rights to the content you upload, and that such content does not violate the rights of any third party.
            </p>
          </section>
          
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. Limitations</h2>
            <p className="mb-4">
              DestinPQ shall not be liable for any direct, indirect, incidental, special, consequential, or punitive damages resulting from your use or inability to use the service.
            </p>
            <p>
              We do not guarantee that our services will be uninterrupted, timely, secure, or error-free. The service is provided "as is" and "as available" without warranties of any kind.
            </p>
          </section>
          
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising under these Terms shall be subject to the exclusive jurisdiction of the courts in India.
            </p>
          </section>
          
          <div className="mt-8 text-center">
            <p className="text-gray-600 mb-4">
              These Terms of Service were last updated on June 15, 2023.
            </p>
            <p>
              For any questions regarding these Terms, please contact us at <a href="mailto:support@destinpq.com" className="text-blue-600 hover:text-blue-800">support@destinpq.com</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TermsOfService; 