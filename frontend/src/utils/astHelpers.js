// AST helper functions shared between components

export function getAstExpr(node) {
  if (!node) return '?';
  if (typeof node === 'string') return node;
  if (node.node === '¬') return `¬(${getAstExpr(node.child)})`;
  if (['∧', '∨', '⊕', '↑', '↓', '→', '↔', '≡'].includes(node.node)) {
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
    } else if (['∧', '∨', '⊕', '↑', '↓', '→', '↔', '≡'].includes(node.node)) {
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
  
  // Unary operators
  if (node.node === '¬') return evalAst(node.child, row) === 0 ? 1 : 0;
  
  // Binary operators
  const left = evalAst(node.left, row);
  const right = evalAst(node.right, row);
  
  if (node.node === '∧') return (left === 1 && right === 1) ? 1 : 0;
  if (node.node === '∨') return (left === 1 || right === 1) ? 1 : 0;
  if (node.node === '⊕') return (left !== right) ? 1 : 0;
  if (node.node === '↑') return (left === 1 && right === 1) ? 0 : 1; // NAND
  if (node.node === '↓') return (left === 1 || right === 1) ? 0 : 1; // NOR
  if (node.node === '→') return (left === 0 || right === 1) ? 1 : 0;
  if (node.node === '↔') return (left === right) ? 1 : 0;
  if (node.node === '≡') return (left === right) ? 1 : 0;
  
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
  
  // For binary operators, return direct left and right subexpressions
  if (['∧', '∨', '⊕', '↑', '↓', '→', '↔', '≡'].includes(step.node.node)) {
    const leftExpr = getAstExpr(step.node.left);
    const rightExpr = getAstExpr(step.node.right);
    return [leftExpr, rightExpr];
  }
  
  // For negation, return the negated expression
  if (step.node.node === '¬') {
    const childExpr = getAstExpr(step.node.child);
    return [childExpr];
  }
  
  return [];
}
