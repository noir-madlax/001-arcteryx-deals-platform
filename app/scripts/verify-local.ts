import { rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const steps: Array<{ label: string; command: string; args: string[] }> = [
  { label: 'unit tests', command: 'npm', args: ['test'] },
  { label: 'config sanity', command: 'npm', args: ['run', 'verify:config'] },
  { label: 'typecheck', command: 'npm', args: ['run', 'typecheck'] },
  { label: 'expo doctor', command: 'npm', args: ['run', 'doctor'] },
  { label: 'live data probe', command: 'npm', args: ['run', 'verify:live-data'] },
  { label: 'iOS export', command: 'npx', args: ['expo', 'export', '--platform', 'ios', '--output-dir', 'dist-check'] },
];

function runStep(step: (typeof steps)[number]) {
  console.log(`\n=== ${step.label} ===`);
  const result = spawnSync(step.command, step.args, {
    stdio: 'inherit',
    shell: false,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`${step.label} failed with exit code ${result.status}`);
  }
}

rmSync('dist-check', { recursive: true, force: true });

try {
  for (const step of steps) runStep(step);
} finally {
  rmSync('dist-check', { recursive: true, force: true });
}

console.log('\nverify_local_ok');
