import React, { useMemo, useState } from 'react';
import {
  EXPORT_OPTIONS,
  buildDefaultSelection,
  computeOptionAvailability,
} from '../utils/exportOptions';

export default function ExportOptionsModal({ isOpen, onClose, onConfirm, data }) {
  const [selectedOptions, setSelectedOptions] = useState(() => buildDefaultSelection());

  const availability = useMemo(() => computeOptionAvailability(data), [data]);
  const availabilityMap = useMemo(
    () =>
      availability.reduce((acc, option) => {
        acc[option.key] = option.available;
        return acc;
      }, {}),
    [availability]
  );

  if (!isOpen) return null;

  const handleToggle = (key) => {
    if (!availabilityMap[key]) return;
    setSelectedOptions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSelectAll = () => {
    setSelectedOptions(buildDefaultSelection());
  };

  const handleDeselectAll = () => {
    setSelectedOptions({});
  };

  const handleConfirm = () => {
    // Sprawdź, czy przynajmniej jedna opcja jest wybrana
    const hasSelection = EXPORT_OPTIONS.some(
      (option) => availabilityMap[option.key] && selectedOptions[option.key]
    );
    if (!hasSelection) {
      alert('Proszę wybrać przynajmniej jedną opcję do wydruku.');
      return;
    }
    onConfirm(selectedOptions);
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-end justify-center bg-black bg-opacity-50 overflow-y-auto"
      style={{ paddingTop: '1rem', paddingBottom: '1rem' }}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[calc(100vh-2rem)] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Wybierz elementy do wydruku</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
              aria-label="Zamknij"
            >
              ×
            </button>
          </div>

          <div className="mb-4 flex gap-2">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
            >
              Zaznacz wszystkie
            </button>
            <button
              onClick={handleDeselectAll}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition"
            >
              Odznacz wszystkie
            </button>
          </div>

          <div className="space-y-3 mb-6">
            {EXPORT_OPTIONS.map(option => {
              const available = availabilityMap[option.key];
              const checked = selectedOptions[option.key] || false;
              
              return (
                <div
                  key={option.key}
                  className={`p-4 border rounded-lg transition ${
                    available
                      ? checked
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white hover:bg-gray-50'
                      : 'border-gray-200 bg-gray-100 opacity-60'
                  }`}
                >
                  <label className="flex items-start cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => handleToggle(option.key)}
                      disabled={!available}
                      className="mt-1 mr-3 w-5 h-5 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                    />
                    <div className="flex-1">
                      <div className="font-semibold text-gray-800">
                        {option.label}
                        {!available && (
                          <span className="ml-2 text-xs text-gray-500">(niedostępne)</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">{option.description}</div>
                    </div>
                  </label>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition font-semibold"
            >
              Anuluj
            </button>
            <button
              onClick={handleConfirm}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition font-semibold"
            >
              Eksportuj do PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

