import { useState, useRef, useEffect } from 'react';
import { askQuestion } from '../services/api';

function ChatInterface() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hej! Jag är din RaceBuddy AI-assistent. Jag kan svara på frågor om Lidingöloppet, träningsplanering och löpning. Vad vill du veta?' 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to last message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user's message
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      // Send question to API
      const response = await askQuestion(input);
      
      // Add AI's response
      const assistantMessage = { 
        role: 'assistant', 
        content: response.response || 'Jag kunde inte generera ett svar just nu. Försök igen senare.'
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      // Add error message
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: 'Jag kunde inte generera ett svar just nu. Försök igen senare.' 
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Suggested questions
  const suggestedQuestions = [
    "Hur ska jag träna inför Lidingöloppet?",
    "Vilka är de svåraste partierna på Lidingöloppet?",
    "Hur lång tid innan loppet bör jag börja träna?",
    "Vilken utrustning behöver jag till Lidingöloppet?"
  ];

  return (
    <div className="bg-gray-900 p-6 rounded-xl shadow-lg max-w-3xl mx-auto flex flex-col h-[600px]">
      <h2 className="text-2xl font-bold text-white mb-4">
        Chatta med RaceBuddy
      </h2>
      
      {/* Message area */}
      <div className="flex-grow overflow-y-auto mb-4 bg-gray-800 rounded-lg p-4">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] p-3 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-[#007aff] text-white' 
                    : 'bg-gray-700 text-gray-100'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 p-3 rounded-lg text-gray-100">
                <div className="loaderimage"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Suggested questions */}
      {messages.length < 3 && (
        <div className="mb-4">
          <p className="text-gray-400 text-sm mb-2">Föreslagna frågor:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => {
                  setInput(question);
                  // Auto-submit if convenient
                  // handleSubmit({ preventDefault: () => {} });
                }}
                className="bg-gray-800 hover:bg-gray-700 text-white text-sm py-1 px-3 rounded-full"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Input area */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ställ en fråga..."
          className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="bg-[#007aff] hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg disabled:opacity-50"
        >
          Skicka
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;