function Footer() {
    return (
      <footer className="bg-black py-4 text-center text-gray-400 border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p>© {new Date().getFullYear()} RaceBuddy. Alla rättigheter förbehållna.</p>
          <p className="text-sm">Personlig träningsplanering för Lidingöloppet</p>
        </div>
      </footer>
    );
  }
  
  export default Footer;