import { useState, useEffect } from 'react';
import { generateICSFile } from '../services/api';

function TrainingCalendar({ trainingPlan }) {
  const [isLoading, setIsLoading] = useState(false);
  const [calendar, setCalendar] = useState([]);
  const [icsLink, setIcsLink] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(1);
  
  // Get calendar entries from training plan
  useEffect(() => {
    if (trainingPlan && trainingPlan.calendar_sessions) {
      setCalendar(trainingPlan.calendar_sessions);
      
      // Generate ICS file
      const generateICS = async () => {
        try {
          setIsLoading(true);
          const icsData = await generateICSFile(trainingPlan);
          if (icsData && icsData.ics_content) {
            // Create Blob and URL for download
            const blob = new Blob([icsData.ics_content], { type: 'text/calendar;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            setIcsLink(url);
          }
        } catch (error) {
          console.error('Error generating ICS file:', error);
        } finally {
          setIsLoading(false);
        }
      };
      
      generateICS();
    }
  }, [trainingPlan]);
  
  // Group training sessions by week
  const weeks = calendar.reduce((acc, session) => {
    const weekNumber = session.week_number;
    if (!acc[weekNumber]) {
      acc[weekNumber] = [];
    }
    acc[weekNumber].push(session);
    return acc;
  }, {});
  
  // Show empty state if no training plan exists
  if (!trainingPlan) {
    return (
      <div className="bg-gray-900 p-6 rounded-xl shadow-lg max-w-3xl mx-auto text-center">
        <h2 className="text-xl font-semibold text-white mb-4">Ingen träningsplan genererad</h2>
        <p className="text-gray-400 mb-4">Gå till "Träningsplanerare" för att skapa en ny träningsplan.</p>
      </div>
    );
  }
  
  const totalWeeks = Object.keys(weeks).length;
  
  return (
    <div className="bg-gray-900 p-6 rounded-xl shadow-lg max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">Din träningsplan</h2>
        
        {icsLink && (
          <a 
            href={icsLink} 
            download={`training_plan_${trainingPlan.plan_summary?.race || 'lidingo'}.ics`}
            className="bg-[#007aff] hover:bg-blue-700 text-white text-sm font-semibold py-2 px-4 rounded-lg flex items-center"
          >
            Ladda ner kalender (.ics)
          </a>
        )}
      </div>
      
      {/* Training overview */}
      <div className="bg-gray-800 p-4 rounded-lg mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">Träningsöversikt</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 p-3 rounded-lg">
            <p className="text-gray-400 text-sm">Totalt antal veckor</p>
            <p className="text-white text-xl font-semibold">{trainingPlan.plan_summary?.total_weeks || totalWeeks}</p>
          </div>
          <div className="bg-gray-700 p-3 rounded-lg">
            <p className="text-gray-400 text-sm">Total distans</p>
            <p className="text-white text-xl font-semibold">{Math.round(trainingPlan.plan_summary?.total_distance_km || 0)} km</p>
          </div>
          <div className="bg-gray-700 p-3 rounded-lg">
            <p className="text-gray-400 text-sm">Träningsdagar per vecka</p>
            <p className="text-white text-xl font-semibold">{trainingPlan.user_data?.training_days_per_week || 0}</p>
          </div>
        </div>
      </div>
      
      {/* Week navigation */}
      <div className="flex justify-between items-center mb-4">
        <button 
          onClick={() => setCurrentWeek(prev => Math.max(1, prev - 1))}
          disabled={currentWeek === 1}
          className="bg-gray-800 text-white py-1 px-3 rounded-lg disabled:opacity-50"
        >
          ← Föregående
        </button>
        
        <div className="text-white font-medium">
          Vecka {currentWeek} av {totalWeeks}
        </div>
        
        <button 
          onClick={() => setCurrentWeek(prev => Math.min(totalWeeks, prev + 1))}
          disabled={currentWeek === totalWeeks}
          className="bg-gray-800 text-white py-1 px-3 rounded-lg disabled:opacity-50"
        >
          Nästa →
        </button>
      </div>
      
      {/* Week's training sessions */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">
          Vecka {currentWeek}: {weeks[currentWeek]?.[0]?.week_focus || 'Träning'}
        </h3>
        
        <div className="space-y-3">
          {weeks[currentWeek]?.map((session, index) => (
            <div key={index} className="bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="text-gray-400 text-xs">{session.day_name}, {session.day_date}</span>
                  <h4 className="text-white font-semibold">{session.pass}</h4>
                </div>
                <span className="bg-[#007aff] text-white text-xs font-medium px-2 py-1 rounded">
                  {/* Show distance as integer */}
                  {Math.round(session.distance_km)} km
                </span>
              </div>
              <p className="text-gray-300 text-sm">{session.fokus}</p>
              {session.pace && (
                <p className="text-gray-400 text-xs mt-1">Tempo: {session.pace}/km</p>
              )}
            </div>
          ))}
          
          {!weeks[currentWeek] || weeks[currentWeek].length === 0 ? (
            <div className="text-center py-6 text-gray-400">
              Inga träningspass planerade för denna vecka.
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default TrainingCalendar;