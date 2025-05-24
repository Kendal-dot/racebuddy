import { useState } from 'react';
import { generateTrainingPlan } from '../services/api';

function PlannerForm({ onPlanGenerated }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Default start date (today) and race date (3 months ahead)
  const today = new Date();
  const defaultRaceDate = new Date(today);
  defaultRaceDate.setMonth(today.getMonth() + 3);
  
  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };
  
  const [formData, setFormData] = useState({
    gender: 'male',
    height_cm: 175,
    weight_kg: 75,
    age: 30,
    fitness_level: 'intermediate',
    race: 'lidingo',
    target_time: '3:00:00',
    start_date: formatDate(today),
    race_date: formatDate(defaultRaceDate),
    training_days_per_week: 4,
    previous_race_times: [],
    injuries: []
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    
    setFormData(prevData => ({
      ...prevData,
      [name]: type === 'number' ? Number(value) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await generateTrainingPlan(formData);
      onPlanGenerated(response);
    } catch (err) {
      setError('Ett fel uppstod vid generering av träningsplanen. Försök igen senare.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 p-6 rounded-xl shadow-lg max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold text-white mb-6">
        Skapa din personliga träningsplan för Lidingöloppet
      </h2>
      
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-white p-4 mb-6 rounded-lg">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Personal information */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Kön
            </label>
            <select
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            >
              <option value="male">Man</option>
              <option value="female">Kvinna</option>
              <option value="other">Annat</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Ålder
            </label>
            <input
              type="number"
              name="age"
              value={formData.age}
              onChange={handleChange}
              min="18"
              max="100"
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Längd (cm)
            </label>
            <input
              type="number"
              name="height_cm"
              value={formData.height_cm}
              onChange={handleChange}
              min="100"
              max="250"
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Vikt (kg)
            </label>
            <input
              type="number"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              min="30"
              max="200"
              step="0.1"
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
          
          {/* Training information */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Konditionsnivå
            </label>
            <select
              name="fitness_level"
              value={formData.fitness_level}
              onChange={handleChange}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            >
              <option value="beginner">Nybörjare</option>
              <option value="intermediate">Medel</option>
              <option value="advanced">Avancerad</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Träningstillfällen per vecka
            </label>
            <select
              name="training_days_per_week"
              value={formData.training_days_per_week}
              onChange={handleChange}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            >
              <option value={3}>3 dagar</option>
              <option value={4}>4 dagar</option>
              <option value={5}>5 dagar</option>
              <option value={6}>6 dagar</option>
              <option value={7}>7 dagar</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Startdatum för träning
            </label>
            <input
              type="date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Tävlingsdatum
            </label>
            <input
              type="date"
              name="race_date"
              value={formData.race_date}
              onChange={handleChange}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Målsättningstid (HH:MM:SS)
            </label>
            <input
              type="text"
              name="target_time"
              value={formData.target_time}
              onChange={handleChange}
              placeholder="03:00:00"
              pattern="[0-9]{1,2}:[0-5][0-9]:[0-5][0-9]"
              className="bg-gray-800 border border-gray-700 text-white rounded-lg py-2 px-4 block w-full"
            />
          </div>
        </div>
        
        <div className="pt-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-[#007aff] hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg w-full flex justify-center items-center"
          >
            {loading ? (
              <>
                <div className="loaderimage mr-3"></div>
                <span>Genererar plan...</span>
              </>
            ) : (
              'Skapa träningsplan'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default PlannerForm;