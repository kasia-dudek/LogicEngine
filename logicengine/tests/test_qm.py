import pytest
import logging
from logicengine.qm import simplify_qm, QMError
from logicengine.kmap import simplify_kmap, KMapError
from logicengine.parser import LogicExpressionError
from logicengine.truth_table import generate_truth_table, TruthTableError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.mark.parametrize("expr,expected_result", [
    ("(A ∧ B) ∨ (¬A ∧ B)", "B"),
    ("A ∧ (B ∨ ¬C)", "A ∧ (B ∨ ¬C)"),
    ("¬A ∧ ¬B", "¬A ∧ ¬B"),
    ("A", "A"),
    ("A ∨ ¬A", "1"),
    ("A ∧ ¬A", "0"),
    ("(A ∧ B ∧ C) ∨ (¬A ∧ B ∧ C)", "B ∧ C"),
    ("(A ∧ B ∧ ¬C ∧ ¬D) ∨ (A ∧ B ∧ C ∧ ¬D)", "A ∧ B ∧ ¬D"),
])
def test_qm_simplify_correct_expressions(expr, expected_result):
    """Sprawdza poprawność uproszczenia QM, zgodność z K-map i tabelą prawdy."""
    try:
        qm_result = simplify_qm(expr)
        assert "result" in qm_result, "Brak klucza 'result' w wyniku QM"
        assert "steps" in qm_result, "Brak klucza 'steps' w wyniku QM"
        assert isinstance(qm_result["steps"], list), "Kroki nie są listą"
        assert len(qm_result["steps"]) >= 2, f"Zbyt mało kroków dla {expr}: {qm_result['steps']}"

        orig_vars = sorted(set(ch for ch in expr if ch.isalpha()))
        expr_qm = qm_result.get("expr_for_tests", qm_result["result"])
        tt_qm = generate_truth_table(expr_qm if expr_qm != '0' else 'A ∧ ¬A', force_vars=orig_vars)
        tt_orig = generate_truth_table(expr, force_vars=orig_vars)
        assert tt_qm == tt_orig, f"Tabela prawdy QM różni się od oryginalnej dla {expr}"

        kmap_result = simplify_kmap(expr)
        assert "result" in kmap_result, "Brak klucza 'result' w wyniku K-map"
        expr_kmap = kmap_result.get("expr_for_tests", kmap_result["result"])
        tt_kmap = generate_truth_table(expr_kmap if expr_kmap != '0' else 'A ∧ ¬A', force_vars=orig_vars)
        assert tt_qm == tt_kmap, f"Tabele prawdy QM i K-map różnią się dla {expr}"

        step_names = [step["step"] for step in qm_result["steps"]]
        assert "Krok 1: Znajdź mintermy" in step_names, "Brak kroku znajdowania mintermów"
        assert "Krok 7: Uproszczone wyrażenie" in step_names, "Brak kroku z uproszczonym wyrażeniem"
        assert "Krok 8: Weryfikacja poprawności" in step_names, "Brak kroku weryfikacji"
        assert qm_result["steps"][-1]["data"]["zgodność"], f"Weryfikacja nie powiodła się dla {expr}"

        logger.info(f"Test passed for {expr}: QM={qm_result['result']}, KMAP={kmap_result['result']}")
    except Exception as e:
        logger.error(f"Błąd w teście dla {expr}: {e}")
        raise

@pytest.mark.parametrize("expr,expected_error", [
    ("A $ B", LogicExpressionError),
    ("A ∧ B ∧ C ∧ D ∧ E", QMError),
    ("(A ∧ B", LogicExpressionError),
    ("A ∨ ", LogicExpressionError),
    ("", LogicExpressionError),
    ("X ∧ Y", LogicExpressionError),
])
def test_qm_invalid_expressions(expr, expected_error):
    """Sprawdza, czy QM zgłasza odpowiednie błędy dla niepoprawnych wyrażeń."""
    with pytest.raises(expected_error) as exc_info:
        simplify_qm(expr)
    logger.info(f"Test niepoprawnego wyrażenia '{expr}' przeszedł: {exc_info.value}")

@pytest.mark.parametrize("expr,expected_result,expected_step", [
    ("A ∨ ¬A", "1", "Krok 2: Tautologia"),
    ("A ∧ ¬A", "0", "Krok 2: Sprzeczność"),
    ("A", "A", "Krok 7: Uproszczone wyrażenie"),
    ("¬A", "¬A", "Krok 7: Uproszczone wyrażenie"),
])
def test_qm_edge_cases(expr, expected_result, expected_step):
    """Sprawdza przypadki brzegowe: tautologia, sprzeczność, pojedyncza zmienna."""
    qm_result = simplify_qm(expr)
    orig_vars = sorted(set(ch for ch in expr if ch.isalpha()))
    expr_qm = qm_result.get("expr_for_tests", qm_result["result"])
    tt_qm = generate_truth_table(expr_qm if expr_qm != '0' else 'A ∧ ¬A', force_vars=orig_vars)
    tt_orig = generate_truth_table(expr, force_vars=orig_vars)
    assert tt_qm == tt_orig, f"Tabela prawdy QM różni się od oryginalnej dla {expr}"
    assert qm_result["result"] == expected_result, f"Niepoprawny wynik dla {expr}: {qm_result['result']} != {expected_result}"
    assert any(step["step"] == expected_step for step in qm_result["steps"]), f"Brak oczekiwanego kroku '{expected_step}' dla {expr}"
    assert qm_result["steps"][-1]["data"]["zgodność"], f"Weryfikacja nie powiodła się dla {expr}"
    logger.info(f"Test przypadku brzegowego '{expr}' przeszedł: wynik={qm_result['result']}")

def test_qm_steps_structure():
    """Sprawdza strukturę i poprawność kroków upraszczania w QM."""
    expr = "(A ∧ B) ∨ (¬A ∧ B)"
    qm_result = simplify_qm(expr)
    steps = qm_result["steps"]

    for step in steps:
        assert "step" in step, f"Krok nie ma pola 'step': {step}"
        assert "data" in step, f"Krok nie ma pola 'data': {step}"
        assert "opis" in step["data"], f"Krok nie ma opisu: {step}"

    step_names = [step["step"] for step in steps]
    expected_steps = [
        "Krok 1: Znajdź mintermy",
        "Krok 2: Grupowanie mintermów według liczby jedynek",
        "Krok 3: Wyznaczanie implikantów pierwszorzędnych",
        "Krok 4: Tabela pokrycia",
        "Krok 5: Zasada implikanty",
        "Krok 6: Minimalne pokrycie (metoda Petricka)",
        "Krok 7: Uproszczone wyrażenie",
        "Krok 8: Weryfikacja poprawności"
    ]
    for expected in expected_steps:
        assert expected in step_names, f"Brak kroku '{expected}' w {step_names}"

    minterms_step = next(step for step in steps if step["step"] == "Krok 1: Znajdź mintermy")
    assert "minterms" in minterms_step["data"], "Brak mintermów w kroku 1"
    assert minterms_step["data"]["minterms"] == [1, 3], f"Niepoprawne mintermy: {minterms_step['data']['minterms']}"

    result_step = next(step for step in steps if step["step"] == "Krok 7: Uproszczone wyrażenie")
    assert result_step["data"]["result"] == "B", f"Niepoprawny wynik w kroku 7: {result_step['data']['result']}"

    verification_step = steps[-1]
    assert verification_step["data"]["zgodność"], "Weryfikacja nie powiodła się"

    logger.info(f"Test struktury kroków dla '{expr}' przeszedł")

def test_qm_kmap_consistency():
    """Sprawdza zgodność wyników QM i K-map dla różnych wyrażeń."""
    expressions = [
        "(A ∧ B) ∨ (¬A ∧ B)",
        "A ∧ (B ∨ ¬C)",
        "(A ∧ B ∧ C) ∨ (¬A ∧ B ∧ C)",
    ]
    for expr in expressions:
        qm_result = simplify_qm(expr)
        kmap_result = simplify_kmap(expr)
        orig_vars = sorted(set(ch for ch in expr if ch.isalpha()))

        expr_qm = qm_result.get("expr_for_tests", qm_result["result"])
        expr_kmap = kmap_result.get("expr_for_tests", kmap_result["result"])

        tt_qm = generate_truth_table(expr_qm if expr_qm != '0' else 'A ∧ ¬A', force_vars=orig_vars)
        tt_kmap = generate_truth_table(expr_kmap if expr_kmap != '0' else 'A ∧ ¬A', force_vars=orig_vars)

        assert tt_qm == tt_kmap, f"Tabele prawdy QM i K-map różnią się dla {expr}"
        logger.info(f"Zgodność QM i K-map dla '{expr}' potwierdzona")