import React from 'react';

const ProgressIndicator = ({ currentStep, totalSteps, stepNames }) => {
  const getStepNumber = (stepName) => {
    if (stepName.includes('Tabela prawdy')) return 1;
    if (stepName.includes('Grupowanie')) return 2;
    if (stepName.includes('implikantów pierwszorzędnych')) return 3;
    if (stepName.includes('Tabela pokrycia')) return 4;
    if (stepName.includes('Implikanty istotne')) return 5;
    if (stepName.includes('Minimalne pokrycie')) return 6;
    if (stepName.includes('Uproszczone wyrażenie')) return 7;
    return 0;
  };

  const steps = [
    { number: 1, name: 'Tabela prawdy', description: 'Znajdź mintermy' },
    { number: 2, name: 'Grupowanie', description: 'Pogrupuj według jedynek' },
    { number: 3, name: 'Implikanty', description: 'Znajdź pierwszorzędne' },
    { number: 4, name: 'Pokrycie', description: 'Stwórz tabelę' },
    { number: 5, name: 'Istotne', description: 'Znajdź kluczowe' },
    { number: 6, name: 'Minimalne', description: 'Wybierz optymalne' },
    { number: 7, name: 'Wynik', description: 'Zminimalizowane wyrażenie' }
  ];

  return (
    <div className="bg-white rounded-xl shadow p-4 mb-6 border border-blue-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Postęp metody Quine-McCluskey</h3>
        <div className="text-sm text-gray-600">
          Krok {currentStep} z {totalSteps}
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;
          const isPending = step.number > currentStep;
          
          return (
            <div key={step.number} className="flex flex-col items-center flex-1">
              <div className="flex items-center">
                {/* Linia łącząca */}
                {index < steps.length - 1 && (
                  <div 
                    className={`h-0.5 flex-1 mx-2 ${
                      isCompleted ? 'bg-green-400' : 'bg-gray-300'
                    }`}
                  />
                )}
                
                {/* Kółko z numerem */}
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    isCompleted 
                      ? 'bg-green-500 text-white' 
                      : isCurrent 
                        ? 'bg-blue-500 text-white animate-pulse' 
                        : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {isCompleted ? '✓' : step.number}
                </div>
                
                {/* Linia łącząca */}
                {index < steps.length - 1 && (
                  <div 
                    className={`h-0.5 flex-1 mx-2 ${
                      isCompleted ? 'bg-green-400' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
              
              {/* Nazwa kroku */}
              <div className="mt-2 text-center">
                <div className={`text-xs font-medium ${
                  isCurrent ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {step.name}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {step.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProgressIndicator;
