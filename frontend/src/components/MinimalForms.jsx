// MinimalForms.jsx
import React from 'react';

/**
 * Component presenting minimal forms (DNF, CNF) from backend /minimal_forms.
 * Focuses only on DNF and CNF with clear legends and explanations.
 *
 * Props:
 *  - data: object (data from API /minimal_forms)
 */
export default function MinimalForms({ data }) {
  if (!data) {
    return (
      <div className="text-center text-gray-500 p-4">
        No data available for minimal forms
      </div>
    );
  }

  const vars = data?.vars || [];
  const dnf = data?.dnf || {};
  const cnf = data?.cnf || {};
  const notes = data?.notes || [];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-6">
      {/* Header with explanation */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl md:text-3xl font-extrabold text-blue-700 tracking-tight">
            Minimal Forms (DNF / CNF)
          </h2>
          {vars.length > 0 && (
            <div className="text-sm text-gray-600 bg-blue-50 px-3 py-1 rounded-full">
              Variables: {vars.join(', ')}
            </div>
          )}
        </div>
        
        {/* Legend */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">Legend:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-blue-700">
            <div>
              <strong>DNF (Disjunctive Normal Form):</strong> Sum of products - expression written as OR of AND terms
            </div>
            <div>
              <strong>CNF (Conjunctive Normal Form):</strong> Product of sums - expression written as AND of OR terms
            </div>
          </div>
          <div className="mt-2 text-xs text-blue-600">
            <strong>Terms:</strong> Number of AND/OR clauses | <strong>Literals:</strong> Number of variable occurrences
          </div>
        </div>
      </div>

      {/* Main content - 2 column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* DNF */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <span className="w-4 h-4 bg-blue-500 rounded-full mr-3"></span>
            DNF (Disjunctive Normal Form)
            <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
              Sum of Products
            </span>
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Minimal Expression:</label>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg font-mono text-sm text-blue-900">
                {dnf?.expr || 'No data'}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Terms (Products)</div>
                <div className="text-lg font-bold text-blue-600">{dnf?.terms || 0}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Total Literals</div>
                <div className="text-lg font-bold text-blue-600">{dnf?.literals || 0}</div>
              </div>
            </div>
            
            <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
              <strong>Example:</strong> (A ∧ ¬B) ∨ (¬A ∧ B) ∨ (A ∧ B)
            </div>
          </div>
        </div>

        {/* CNF */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <span className="w-4 h-4 bg-green-500 rounded-full mr-3"></span>
            CNF (Conjunctive Normal Form)
            <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
              Product of Sums
            </span>
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">Minimal Expression:</label>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg font-mono text-sm text-green-900">
                {cnf?.expr || 'No data'}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Terms (Sums)</div>
                <div className="text-lg font-bold text-green-600">{cnf?.terms || 0}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Total Literals</div>
                <div className="text-lg font-bold text-green-600">{cnf?.literals || 0}</div>
              </div>
            </div>
            
            <div className="text-xs text-gray-600 bg-green-50 p-2 rounded">
              <strong>Example:</strong> (A ∨ B) ∧ (¬A ∨ ¬B) ∧ (A ∨ ¬B)
            </div>
          </div>
        </div>
      </div>

      {/* Notes section */}
      {notes.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-800 mb-3 flex items-center">
            <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
            Analysis Notes
          </h3>
          <ul className="space-y-2">
            {notes.map((note, index) => (
              <li key={index} className="text-sm text-yellow-700 bg-yellow-100 p-2 rounded">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}