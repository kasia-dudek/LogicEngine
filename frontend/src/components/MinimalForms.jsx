import React, { useState, useEffect } from "react";

/**
 * MinimalForms - wyświetla formy minimalne wyrażenia logicznego
 * Props: expr (string) - wyrażenie do analizy
 */
export default function MinimalForms({ expr }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log('MinimalForms useEffect - expr:', expr);
    
    if (!expr?.trim()) {
      console.log('MinimalForms - empty expr, returning');
      setData(null);
      setError("");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");
    setData(null);

    const fetchData = async () => {
      try {
        console.log('MinimalForms - starting fetch for:', expr);
        
        // First standardize the expression like other components do
        let standardizedExpr = expr;
        try {
          const standardizeResponse = await fetch("http://127.0.0.1:8000/standardize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expr }),
          });
          
          if (standardizeResponse.ok) {
            const standardizeResult = await standardizeResponse.json();
            standardizedExpr = standardizeResult.standardized;
            console.log('MinimalForms - standardized expr:', standardizedExpr);
          }
        } catch (e) {
          console.log('MinimalForms - standardization failed, using original:', e);
        }
        
        const response = await Promise.race([
          fetch("http://127.0.0.1:8000/minimal_forms", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expr: standardizedExpr }),
          }),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout: Przetwarzanie trwa zbyt długo')), 15000)
          )
        ]);

        console.log('MinimalForms - response received:', response.status);

        if (cancelled) return;

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        console.log('MinimalForms - result:', result);
        if (cancelled) return;

        setData(result);
      } catch (err) {
        console.log('MinimalForms - error:', err);
        if (cancelled) return;
        setError(err.message);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => { cancelled = true; };
  }, [expr]);

  if (loading) {
    return (
      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-xl text-gray-700">
        Ładowanie form minimalnych…
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
        Błąd: {error}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const forms = [
    { label: "DNF", value: data.dnf?.expr || "—" },
    { label: "CNF", value: data.cnf?.expr || "—" },
    { label: "ANF", value: data.anf?.expr || "—" },
    { label: "NOR", value: data.nor?.expr || "—" },
    { label: "NAND", value: data.nand?.expr || "—" },
    { label: "AND", value: data.andonly?.expr || "—" },
    { label: "OR", value: data.oronly?.expr || "—" },
  ];

  return (
    <div className="mt-8">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">Minimal forms</h3>
      
      <div className="overflow-x-auto">
        <table className="min-w-[320px] border border-gray-300 rounded-xl text-sm">
          <tbody>
            {forms.map(({ label, value }) => (
              <tr key={label}>
                <td className="px-3 py-2 border-b bg-gray-100 font-semibold w-24">
                  {label}
                </td>
                <td className="px-3 py-2 border-b font-mono">{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.notes?.length > 0 && (
        <ul className="mt-2 text-xs text-gray-600 list-disc ml-5">
          {data.notes.map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
