// AST helper functions shared between components

export function getAstExpr(node) {
  if (!node) return '?';
  if (typeof node === 'string') return node;
  if (node.node === '¬') return `¬(${getAstExpr(node.child)})`;
  if (['∧', '∨', '→', '↔'].includes(node.node)) {
    return `(${getAstExpr(node.left)} ${node.node} ${getAstExpr(node.right)})`;
  }
  return '?';
}

export function getAstStepsNoVars(ast) {
  const steps = [];
  const seen = new Set();

  function traverse(node) {
    if (!node || typeof node === 'string') return;

    if (node.node === '¬') {
      traverse(node.child);
      const expr = `¬(${getAstExpr(node.child)})`;
      if (!seen.has(expr)) {
        steps.push({ expr, node });
        seen.add(expr);
      }
    } else if (['∧', '∨', '→', '↔'].includes(node.node)) {
      traverse(node.left);
      traverse(node.right);
      const expr = `(${getAstExpr(node.left)} ${node.node} ${getAstExpr(node.right)})`;
      if (!seen.has(expr)) {
        steps.push({ expr, node });
        seen.add(expr);
      }
    }
  }

  traverse(ast);
  return steps;
}

export function evalAst(node, row) {
  if (!node) return null;
  if (typeof node === 'string') {
    if (node === '0') return 0;
    if (node === '1') return 1;
    return row[node] || 0;
  }
  if (node.node === '¬') return 1 - evalAst(node.child, row);
  if (node.node === '∧') return evalAst(node.left, row) && evalAst(node.right, row);
  if (node.node === '∨') return evalAst(node.left, row) || evalAst(node.right, row);
  if (node.node === '→') return (1 - evalAst(node.left, row)) || evalAst(node.right, row);
  if (node.node === '↔') return evalAst(node.left, row) === evalAst(node.right, row);
  return null;
}

export function computeStepValues(ast, truthTable) {
  const steps = getAstStepsNoVars(ast);
  return steps.map(step => ({
    ...step,
    values: truthTable.map(row => evalAst(step.node, row))
  }));
}

export function getStepArgs(step) {
  if (!step.node) return [];
  if (typeof step.node === 'string') return [step.node];
  if (step.node.node === '¬') return getStepArgs({ node: step.node.child });
  if (['∧', '∨', '→', '↔'].includes(step.node.node)) {
    return [
      ...getStepArgs({ node: step.node.left }),
      ...getStepArgs({ node: step.node.right })
    ];
  }
  return [];
}
