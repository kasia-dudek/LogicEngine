import React, { useEffect, useMemo, useState } from 'react';
import ColoredExpression from './ColoredExpression';
import { highlightBySpan, highlightBySpansCP } from './highlightBySpan';

/** Małe helpery UI */
function MetricBadge({ label, before, after }) {
  const up = after > before;
  const down = after < before;
  return (
    <div className="flex items-center gap-1 text-sm">
      <span className="text-gray-600">{label}:</span>
      <span className="font-mono">{before}</span>
      <span className={up ? 'text-red-600' : down ? 'text-green-600' : 'text-gray-500'}>
        {up ? '↑' : down ? '↓' : '→'}
      </span>
      <span className="font-mono">{after}</span>
    </div>
  );
}

/** fetch z timeoutem (5s) + BEZPIECZNY CATCH na AbortError */
async function fetchJSON(url, opts = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort('timeout'), timeoutMs);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, data, status: res.status, aborted: false };
  } catch (err) {
    const aborted = err?.name === 'AbortError';
    return {
      ok: false,
      data: { error: aborted ? 'Request aborted (timeout/unmount)' : (err?.message || String(err)) },
      status: 0,
      aborted,
    };
  } finally {
    clearTimeout(id);
  }
}

function TutorialPanel({
  currentExpr,
  onHistoryStep,
  onExpressionChange,
  onHighlight,
}) {
  const apiUrl = useMemo(() => {
    const envUrl = (process.env.REACT_APP_API_URL || '').replace(/\/+$/, '');
    const fallbackUrl = 'http://127.0.0.1:8000';
    const finalUrl = envUrl || fallbackUrl;
    return finalUrl;
  }, []);
  const [rules, setRules] = useState([]);
  const [activeRule, setActiveRule] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastMetrics, setLastMetrics] = useState(null);

  /** pobranie listy reguł na starcie (jeśli backend skonfigurowany) */
  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!apiUrl) return;
      const { ok, data, status } = await fetchJSON(`${apiUrl}/rules/list`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!mounted) return;
      if (!ok) {
        setError(`Nie udało się pobrać listy praw (HTTP ${status}).`);
        return;
      }
      setRules(Array.isArray(data.rules) ? data.rules : []);
    }
    load();
    return () => { mounted = false; };
  }, [apiUrl]);

  const loadMatches = async (rule) => {
    if (!apiUrl) {
      setError('Backend nie jest skonfigurowany (REACT_APP_API_URL).');
      return;
    }
    setActiveRule(rule);
    setLoading(true);
    setError('');
    setMatches([]);
    
    const requestBody = { expr: currentExpr, ruleId: rule.id };
    
    try {
      const { ok, data, status } = await fetchJSON(`${apiUrl}/rules/matches`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      if (!ok) throw new Error(data?.error || `Błąd pobierania dopasowań (HTTP ${status}).`);
      const items = Array.isArray(data.matches) ? data.matches : [];
      setMatches(items);
      if (items.length === 0) onHighlight(null);
    } catch (e) {
      setError(e.message || 'Błąd pobierania dopasowań.');
    } finally {
      setLoading(false);
    }
  };

  const applyMatch = async (m) => {
    if (!apiUrl) {
      setError('Backend nie jest skonfigurowany (REACT_APP_API_URL).');
      return;
    }
    if (!activeRule) return;
    setLoading(true);
    setError('');
    try {
      const { ok, data, status } = await fetchJSON(`${apiUrl}/rules/apply`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expr: currentExpr, ruleId: activeRule.id, matchId: m.matchId })
      }, 10000); // 10s dla „apply” na wszelki wypadek
      if (!ok) throw new Error(data?.error || `Błąd zastosowania reguły (HTTP ${status}).`);

      const metricsBefore = data.metricsBefore || { operators: 0, literals: 0, neg_depth_sum: 0 };
      const metricsAfter = data.metricsAfter || { operators: 0, literals: 0, neg_depth_sum: 0 };

      const worsened =
        metricsAfter.operators > metricsBefore.operators ||
        metricsAfter.literals > metricsBefore.literals ||
        metricsAfter.neg_depth_sum > metricsBefore.neg_depth_sum;

      if (worsened) {
        // eslint-disable-next-line no-alert
        const cont = window.confirm('Krok może skomplikować wyrażenie – kontynuować?');
        if (!cont) { setLoading(false); return; }
      }

      onHistoryStep({
        step: Date.now(),
        ruleName: activeRule.name,
        beforeStr: currentExpr,
        afterStr: data.exprAfter,
        focusPretty: m.focusPretty
      });
      setLastMetrics({ before: metricsBefore, after: metricsAfter });
      onExpressionChange(data.exprAfter);
      setMatches([]);
      onHighlight(null);
    } catch (e) {
      setError(e.message || 'Błąd zastosowania reguły.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-blue-100 p-4 shadow">
      <div className="mb-4">
        <div className="text-xs text-blue-700 font-semibold uppercase mb-2">Paleta praw</div>
        {!apiUrl && (
          <div className="mb-2 text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded p-2">
            Uwaga: nie ustawiono <code>REACT_APP_API_URL</code>. Panel tutorialowy wymaga backendu.
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          {rules.map(r => (
            <button
              key={r.id}
              className={`px-3 py-1 rounded-full text-sm border ${
                activeRule && activeRule.id === r.id
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-gray-100 text-blue-700 border-blue-200 hover:bg-blue-100'
              }`}
              onClick={() => loadMatches(r)}
              disabled={loading}
            >
              {r.name}
            </button>
          ))}
          {rules.length === 0 && (
            <span className="text-gray-500 text-sm">(Brak danych lub backend niedostępny)</span>
          )}
        </div>
      </div>

      {loading && <div className="text-gray-500">Ładowanie…</div>}
      {error && <div className="text-red-600">{error}</div>}

      {activeRule && !loading && matches.length === 0 && (
        <div className="text-gray-500 italic">Brak miejsc do zastosowania dla tego prawa.</div>
      )}

      {matches.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-blue-700 font-semibold uppercase">Dopasowania</div>
          {matches.map((m) => (
            <div key={m.matchId} className="p-3 rounded-xl border border-blue-100 bg-blue-50 flex items-center justify-between">
              <div>
                <div className="text-sm">
                  <span className="font-semibold">Fragment:</span>{' '}
                  {m.before_highlight_spans_cp && m.before_highlight_spans_cp.length > 0 && m.before_str ? (
                    <span className="font-mono whitespace-pre">
                      {highlightBySpansCP(
                        m.before_str,
                        m.before_highlight_spans_cp,
                        "bg-red-50 text-red-800 ring-1 ring-red-200 rounded px-0.5"
                      )}
                    </span>
                  ) : m.before_span && m.before_str ? (
                    <span className="font-mono whitespace-pre">
                      {highlightBySpan(
                        m.before_str,
                        m.before_span,
                        "bg-red-50 text-red-800 ring-1 ring-red-200 rounded px-0.5"
                      )}
                    </span>
                  ) : (
                  <span className="font-mono">{m.focusPretty}</span>
                  )}
                </div>
                <div className="text-sm">
                  <span className="font-semibold">Podgląd po zastosowaniu:</span>{' '}
                  {m.after_highlight_spans_cp && m.after_highlight_spans_cp.length > 0 && m.after_str ? (
                    <span className="font-mono whitespace-pre">
                      {highlightBySpansCP(
                        m.after_str,
                        m.after_highlight_spans_cp,
                        "bg-green-50 text-green-800 ring-1 ring-green-200 rounded px-0.5"
                      )}
                    </span>
                  ) : m.after_span && m.after_str ? (
                    <span className="font-mono whitespace-pre">
                      {highlightBySpan(
                        m.after_str,
                        m.after_span,
                        "bg-green-50 text-green-800 ring-1 ring-green-200 rounded px-0.5"
                      )}
                    </span>
                  ) : (
                  <span className="font-mono">{m.previewExpr}</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  className="px-3 py-1 rounded bg-gray-100 text-blue-700 border border-blue-200"
                  onMouseEnter={() => {
                    // Pass object with text and spans for proper highlighting
                    if (m.before_highlight_spans_cp && m.before_highlight_spans_cp.length > 0 && m.before_str) {
                      onHighlight({
                        text: m.before_str,
                        spans: m.before_highlight_spans_cp,
                        type: 'before'
                      });
                    } else if (m.before_span && m.before_str) {
                      // Fallback to single span
                      onHighlight({
                        text: m.before_str,
                        span: m.before_span,
                        type: 'before'
                      });
                    } else {
                      // Fallback to text only for compatibility
                      onHighlight(m.focusPretty || m.before_str || '');
                    }
                  }}
                  onMouseLeave={() => onHighlight(null)}
                >
                  Podświetl
                </button>
                <button
                  className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-60"
                  onClick={() => applyMatch(m)}
                  disabled={loading}
                >
                  Zastosuj
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {lastMetrics && (
        <div className="mt-4 p-3 rounded-xl border border-blue-100 bg-white">
          <div className="text-xs text-blue-700 font-semibold uppercase mb-2">Metryki</div>
          <div className="flex gap-6">
            <MetricBadge label="Operatory" before={lastMetrics.before.operators} after={lastMetrics.after.operators} />
            <MetricBadge label="Literały" before={lastMetrics.before.literals} after={lastMetrics.after.literals} />
            <MetricBadge label="Suma gł. negacji" before={lastMetrics.before.neg_depth_sum} after={lastMetrics.after.neg_depth_sum} />
          </div>
        </div>
      )}
    </div>
  );
}

export default TutorialPanel;
