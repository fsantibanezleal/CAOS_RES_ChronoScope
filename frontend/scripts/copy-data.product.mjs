import { copyFileSync, existsSync, lstatSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const PREFIX = 'data/derived/';

// The local generation inventory also names the research documents served by the site.
export default function copyResearchDocuments({ derived, out, repo }) {
  const workflow = JSON.parse(readFileSync(join(repo, 'scripts/local/workflow.json'), 'utf8'));
  const paths = workflow.stage_inputs.filter(path => path.startsWith(PREFIX)).map(path => path.slice(PREFIX.length));
  // Stage generation produces the common comparison from the staged inputs.
  paths.push('reevaluation.json');
  const copied = [];
  const problems = [];
  for (const path of new Set(paths)) {
    if (!/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(path) || path.split('/').some(part => part === '.' || part === '..')) {
      problems.push('Invalid research document path: ' + path);
      continue;
    }
    const source = join(derived, path);
    const destination = join(out, path);
    if (!existsSync(source) || !lstatSync(source).isFile()) {
      problems.push('Missing research document: ' + path);
      continue;
    }
    if (existsSync(destination)) continue;
    mkdirSync(dirname(destination), { recursive: true });
    copyFileSync(source, destination);
    copied.push(path);
  }
  return { copied, absent: [], problems };
}
