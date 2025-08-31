import React from 'react';
import Head from 'next/head';
import ChatInterface from '@/components/chat/ChatInterface';

const HomePage: React.FC = () => {
  return (
    <>
      <Head>
        <title>Gain - AI Assistant</title>
        <meta name="description" content="Gain AI Assistant - Your intelligent conversation partner" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gray-50 text-gray-900">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold gradient-text">
                  Gain
                </h1>
                <span className="ml-3 text-gray-600 text-sm">
                  AI Assistant Platform
                </span>
              </div>
              <div className="text-sm text-gray-500">
                Desktop Version
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-8rem)]">
            {/* Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
                <h3 className="text-lg font-semibold mb-4 gradient-text">
                  Welcome to Gain
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed mb-4">
                  Your intelligent AI assistant is ready to help with questions, 
                  analysis, and conversations.
                </p>
                <div className="space-y-2 text-sm text-gray-500">
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    AI Assistant Online
                  </div>
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    Real-time Responses
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
                <h4 className="text-md font-semibold mb-3 text-gray-900">
                  Quick Tips
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Ask questions in natural language</li>
                  <li>• Use Shift+Enter for line breaks</li>
                  <li>• Messages are limited to 2000 characters</li>
                  <li>• Desktop only (1024px+ required)</li>
                </ul>
              </div>
            </div>

            {/* Chat Interface */}
            <div className="lg:col-span-3">
              <ChatInterface className="h-full" />
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="text-center text-sm text-gray-500">
              <p>
                Gain AI Assistant Platform - Built with Next.js and FastAPI
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
};

export default HomePage;