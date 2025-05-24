// src/App.jsx
import { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import PlannerForm from './components/PlannerForm';
import TrainingCalendar from './components/TrainingCalendar';
import ChatInterface from './components/ChatInterface';

function App() {
  const [trainingPlan, setTrainingPlan] = useState(null);
  const [activeTab, setActiveTab] = useState('planner'); // 'planner', 'calendar', 'chat'
  
  // Function to handle new training plan
  const handleNewTrainingPlan = (plan) => {
    setTrainingPlan(plan);
    setActiveTab('calendar'); // Switch to calendar view after plan generation
  };

  return (
    <div className="flex flex-col min-h-screen bg-black">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-grow p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          {activeTab === 'planner' && (
            <PlannerForm onPlanGenerated={handleNewTrainingPlan} />
          )}
          
          {activeTab === 'calendar' && (
            <TrainingCalendar trainingPlan={trainingPlan} />
          )}
          
          {activeTab === 'chat' && (
            <ChatInterface />
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

export default App;