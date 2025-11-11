export const EXPORT_SCHEMA_VERSION = 'logic-engine-export-v1';

export const EXPORT_OPTIONS = [
  { key: 'summary', label: 'Podsumowanie', description: 'Wyrażenie, pokrycie prawdy, ONP, tautologia, sprzeczność' },
  { key: 'dnf_cnf', label: 'DNF i CNF', description: 'Formy minimalne (suma iloczynów i iloczyn sum)' },
  { key: 'ast', label: 'Drzewo składniowe (AST)', description: 'Wizualizacja struktury wyrażenia' },
  { key: 'truth_table', label: 'Tabela prawdy', description: 'Pełna tabela wartości logicznych' },
  { key: 'laws', label: 'Prawa logiczne', description: 'Kroki upraszczania z użyciem praw logicznych' },
  { key: 'qm', label: 'Quine-McCluskey', description: 'Kroki algorytmu Quine-McCluskey' },
  { key: 'kmap', label: 'Mapa Karnaugh', description: 'Wizualizacja i grupowanie mintermów' },
];

export const buildDefaultSelection = (options = EXPORT_OPTIONS, { availableOnly = false } = {}) =>
  options.reduce((acc, option) => {
    if (!availableOnly || option.available !== false) {
      acc[option.key] = true;
    }
    return acc;
  }, {});

export const isExportOptionAvailable = (key, data) => {
  if (!data) return false;

  switch (key) {
    case 'summary':
      return true;
    case 'dnf_cnf':
      return Boolean(data.minimal_forms?.dnf || data.minimal_forms?.cnf);
    case 'ast':
      return Boolean(data.ast);
    case 'truth_table':
      return Boolean(data.truth_table && data.truth_table.length > 0);
    case 'laws':
      return true;
    case 'qm':
      return Boolean(data.qm?.steps && data.qm.steps.length > 0);
    case 'kmap':
      return Boolean((data.kmap_simplification || data.kmap)?.kmap);
    default:
      return false;
  }
};

export const computeOptionAvailability = (data) =>
  EXPORT_OPTIONS.map((option) => ({
    ...option,
    available: isExportOptionAvailable(option.key, data),
  }));

