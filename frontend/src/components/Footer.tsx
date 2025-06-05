import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="mb-4">
              <Logo inverted={true} />
            </div>
            <p className="text-sm text-gray-600">
              DestinPQ offers AI-powered tools for content creators, including our lyrics extraction technology that provides accurate transcription and transliteration for multiple languages.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800 tracking-wider uppercase mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <a href="https://www.destinpq.com/" className="text-sm text-blue-600 hover:text-blue-800" target="_blank" rel="noopener noreferrer">
                  Main Website
                </a>
              </li>
              <li>
                <Link to="/contact" className="text-sm text-blue-600 hover:text-blue-800">
                  Contact Support
                </Link>
              </li>
              <li>
                <a href="#" className="text-sm text-blue-600 hover:text-blue-800">
                  API Documentation
                </a>
              </li>
              <li>
                <Link to="/brand" className="text-sm text-blue-600 hover:text-blue-800">
                  Brand Guidelines
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800 tracking-wider uppercase mb-4">Legal</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/privacy-policy" className="text-sm text-blue-600 hover:text-blue-800">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms-of-service" className="text-sm text-blue-600 hover:text-blue-800">
                  Terms of Service
                </Link>
              </li>
              <li>
                <a href="https://www.destinpq.com/privacy-policy" className="text-sm text-blue-600 hover:text-blue-800" target="_blank" rel="noopener noreferrer">
                  DestinPQ Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-center text-sm text-gray-500">
            © {new Date().getFullYear()} DestinPQ LLP. All rights reserved. <a href="https://www.destinpq.com/" className="text-blue-600 hover:text-blue-800" target="_blank" rel="noopener noreferrer">www.destinpq.com</a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 