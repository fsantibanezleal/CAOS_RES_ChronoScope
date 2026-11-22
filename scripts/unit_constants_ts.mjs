// Inventory authored numeric expressions with the TypeScript compiler, never a text regex.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const require = createRequire(path.join(request.parserRoot, 'frontend', 'package.json'));
const ts = require('typescript');
const files = [];
for (const filename of request.files) {
  const source = fs.readFileSync(filename, 'utf8');
  const tree = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true,
    ts.getScriptKindFromFileName(filename));
  if (tree.parseDiagnostics.length) {
    throw new Error(`${filename}: ${tree.parseDiagnostics.map(d => ts.flattenDiagnosticMessageText(d.messageText, '\n')).join('; ')}`);
  }
  const entries = [];
  const scopeOf = node => {
    const names = [];
    for (let current = node.parent; current; current = current.parent) {
      if (ts.isFunctionDeclaration(current) || ts.isMethodDeclaration(current) || ts.isClassDeclaration(current)) {
        if (current.name) names.unshift(current.name.getText(tree));
      } else if (ts.isArrowFunction(current) || ts.isFunctionExpression(current)) {
        if (ts.isVariableDeclaration(current.parent)) names.unshift(current.parent.name.getText(tree));
      }
    }
    return names.join('.') || '<module>';
  };
  const visit = node => {
    if (ts.isNumericLiteral(node)) {
      const signed = ts.isPrefixUnaryExpression(node.parent) &&
        [ts.SyntaxKind.MinusToken, ts.SyntaxKind.PlusToken].includes(node.parent.operator) ? node.parent : node;
      const position = tree.getLineAndCharacterOfPosition(signed.getStart(tree));
      let statement = signed;
      while (statement.parent && !ts.isStatement(statement) && !ts.isVariableDeclaration(statement) &&
             !ts.isPropertyAssignment(statement) && !ts.isParameter(statement)) statement = statement.parent;
      entries.push({line: position.line + 1, column: position.character, literal: signed.getText(tree),
        scope: scopeOf(node), context: statement.getText(tree).replace(/\s+/g, ' '),
        parent: ts.SyntaxKind[signed.parent.kind]});
    }
    ts.forEachChild(node, visit);
  };
  visit(tree);
  files.push({path: filename, entries});
}
process.stdout.write(JSON.stringify({compiler: ts.version, files}));
