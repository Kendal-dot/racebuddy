import { useState } from 'react';

function Header({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'planner', label: 'Träningsplanerare' },
    { id: 'calendar', label: 'Kalender' },
    { id: 'chat', label: 'Chat' },
  ];

  return (
    <header className="bg-black border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-[#007aff] text-2xl font-bold">RaceBuddy</span>
            </div>
          </div>
          
          <nav className="flex space-x-4 items-center">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3 py-2 rounded-md text-sm font-medium
                  ${activeTab === item.id
                    ? 'bg-[#007aff] text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;