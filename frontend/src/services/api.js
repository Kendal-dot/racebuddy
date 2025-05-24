const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

// Training plan API calls
export const generateTrainingPlan = async (userData) => {
  try {
    const response = await fetch(`${API_URL}/training/generate-ai-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating training plan:', error);
    throw error;
  }
};

// Chat API calls
export const askQuestion = async (question) => {
  try {
    const response = await fetch(`${API_URL}/chat/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: question,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error asking question:', error);
    throw error;
  }
};

// Calendar API calls
export const generateICSFile = async (planData) => {
  try {
    const response = await fetch(`${API_URL}/training/generate-ics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(planData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating ICS file:', error);
    throw error;
  }
};