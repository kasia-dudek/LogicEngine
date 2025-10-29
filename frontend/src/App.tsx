import React, { useState, useEffect } from 'react';
import ResultScreen from './components/ResultScreen';
import DefinitionsScreen from './components/DefinitionsScreen';
import ExpressionHistory from './components/ExpressionHistory';
import StartScreen from './components/StartScreen';
import PrintableResults from './components/PrintableResults';

function App() {
  const [screen, setScreen] = useState('start');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [printData, setPrintData] = useState(null);

  // Obsługa URL routing dla /print
  useEffect(() => {
    const handleRoute = () => {
      const path = window.location.pathname;
      if (path === '/print') {
        // Sprawdź czy są dane w sessionStorage
        const storedData = sessionStorage.getItem('printData');
        const storedInput = sessionStorage.getItem('printInput');
        
        if (storedData && storedInput) {
          try {
            setPrintData({ data: JSON.parse(storedData), input: storedInput });
            setScreen('print');
          } catch (e) {
            console.error('Error parsing stored print data:', e);
            window.location.href = '/';
          }
        } else {
          window.location.href = '/';
        }
      } else if (path === '/' && screen === 'print') {
        setScreen('start');
      }
    };

    handleRoute();
    window.addEventListener('popstate', handleRoute);
    return () => window.removeEventListener('popstate', handleRoute);
  }, [screen]);

  const saveToHistory = (expression, result) => {
    const HISTORY_KEY = 'logicengine_history';
    const MAX_HISTORY = 50;
    const id = new Date().toISOString();
    let history: any[] = [];
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      if (data) history = JSON.parse(data);
    } catch {}
    
    // Sprawdź czy wyrażenie już istnieje w historii
    const existingIndex = history.findIndex(item => item.expression === expression);
    
    if (existingIndex !== -1) {
      // Jeśli wyrażenie już istnieje, usuń stary wpis i dodaj nowy na początku
      history.splice(existingIndex, 1);
    }
    
    // Dodaj nowy wpis na początku
    history.unshift({ id, expression, result });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  };

  const handleAnalyze = async (input) => {
    setInput(input);
    setScreen('result');
    // Historia będzie zapisana po analizie w ResultScreen
  };

  const handleShowDefinitions = () => {
    setScreen('definitions');
  };

  const handleShowHistory = () => {
    setScreen('history');
  };

  const handleLoadHistory = (item) => {
    setInput(item.expression);
    setScreen('result');
  };

  const handleExportToPrint = (data, input) => {
    // Zapisz dane w sessionStorage
    sessionStorage.setItem('printData', JSON.stringify(data));
    sessionStorage.setItem('printInput', input);
    
    // Przejdź do /print
    window.history.pushState({}, '', '/print');
    setPrintData({ data, input });
    setScreen('print');
  };

  const handleBackFromPrint = () => {
    // Wyczyść dane z sessionStorage
    sessionStorage.removeItem('printData');
    sessionStorage.removeItem('printInput');
    
    // Wróć do poprzedniej strony
    window.history.back();
    setScreen('start');
  };

  return (
    <div className="min-h-screen">
      {screen === 'start' && (
        <>
          <StartScreen
            onSubmit={handleAnalyze}
            onDefinitions={handleShowDefinitions}
            onHistory={handleShowHistory}
          />
        </>
      )}
      {screen === 'result' && <ResultScreen input={input} onBack={() => setScreen('start')} saveToHistory={saveToHistory} onExportToPrint={handleExportToPrint} onShowDefinitions={handleShowDefinitions} />}
      {screen === 'definitions' && <DefinitionsScreen onBack={() => setScreen('start')} />}
      {screen === 'history' && <ExpressionHistory onLoad={handleLoadHistory} onBack={() => setScreen('start')} />}
      {screen === 'print' && printData && (
        <PrintableResults 
          data={printData.data} 
          input={printData.input} 
          onBack={handleBackFromPrint}
        />
      )}
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
          <div className="bg-white p-6 rounded shadow text-lg">Ładowanie...</div>
        </div>
      )}
      {error && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow z-50">
          {error}
        </div>
      )}
    </div>
  );
}

export default App;
