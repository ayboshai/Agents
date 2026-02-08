/* @vitest-environment node */
import { describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

type RunResult = {
  status: number | null;
  stdout: string;
  stderr: string;
};

function run(cmd: string, args: string[], cwd: string, extraEnv?: Record<string, string>): RunResult {
  const res = spawnSync(cmd, args, {
    cwd,
    encoding: 'utf-8',
    env: { ...process.env, ...(extraEnv ?? {}) },
  });
  return {
    status: res.status,
    stdout: (res.stdout ?? '').toString(),
    stderr: (res.stderr ?? '').toString(),
  };
}

function runOk(cmd: string, args: string[], cwd: string, extraEnv?: Record<string, string>): RunResult {
  const res = run(cmd, args, cwd, extraEnv);
  if (res.status !== 0) {
    throw new Error(
      [
        `Expected success but got exit code ${res.status} for: ${cmd} ${args.join(' ')}`,
        '--- stdout ---',
        res.stdout,
        '--- stderr ---',
        res.stderr,
      ].join('\n'),
    );
  }
  return res;
}

function runFail(cmd: string, args: string[], cwd: string, extraEnv?: Record<string, string>): RunResult {
  const res = run(cmd, args, cwd, extraEnv);
  if (res.status === 0) {
    throw new Error(
      [
        `Expected failure but got exit code 0 for: ${cmd} ${args.join(' ')}`,
        '--- stdout ---',
        res.stdout,
        '--- stderr ---',
        res.stderr,
      ].join('\n'),
    );
  }
  return res;
}

function git(cwd: string, args: string[]): string {
  const res = runOk('git', args, cwd);
  return res.stdout.trim();
}

function initTempRepo(): { dir: string } {
  const dir = mkdtempSync(join(tmpdir(), 'cmas-os-guards-'));
  return { dir };
}

function writeJson(path: string, value: unknown): void {
  writeFileSync(path, JSON.stringify(value, null, 2) + '\n', 'utf-8');
}

describe('swarm guard contracts (node integration)', () => {
  it('policy_guard: blocks docs edits when next_phase=QA_CONTRACT', () => {
    const { dir } = initTempRepo();

    // Copy the enforcement package into the temp repo (self-contained).
    cpSync(join(process.cwd(), 'swarm'), join(dir, 'swarm'), { recursive: true });

    // Minimal state: next_phase drives the expected role.
    writeJson(join(dir, 'swarm_state.json'), {
      schema_version: '1.0',
      current_phase: 'ARCHITECT',
      next_phase: 'QA_CONTRACT',
      is_locked: false,
      required_phase_sequence: [
        'ARCHITECT',
        'QA_CONTRACT',
        'BACKEND',
        'ANALYST_CI_GATE',
        'FRONTEND',
        'QA_E2E',
        'ANALYST_FINAL',
      ],
      history: [],
    });

    git(dir, ['init']);
    git(dir, ['add', 'swarm', 'swarm_state.json']);
    git(dir, ['-c', 'user.name=CI', '-c', 'user.email=ci@example.com', 'commit', '-m', 'base']);
    const baseSha = git(dir, ['rev-parse', 'HEAD']);

    mkdirSync(join(dir, 'docs'), { recursive: true });
    writeFileSync(join(dir, 'docs', 'note.md'), '# note\n', 'utf-8');
    git(dir, ['add', 'docs/note.md']);
    git(dir, ['-c', 'user.name=CI', '-c', 'user.email=ci@example.com', 'commit', '-m', 'docs change']);
    const headSha = git(dir, ['rev-parse', 'HEAD']);

    const res = runFail('python3', ['-m', 'swarm.policy_guard', '--base', baseSha, '--head', headSha, '--json'], dir);

    const payload = JSON.parse(res.stdout) as { ok: boolean; violations: Array<{ path: string }> };
    expect(payload.ok).toBe(false);
    expect(payload.violations.some((v) => v.path === 'docs/note.md')).toBe(true);
  });

  it('policy_guard: allows docs edits when next_phase=ARCHITECT', () => {
    const { dir } = initTempRepo();

    cpSync(join(process.cwd(), 'swarm'), join(dir, 'swarm'), { recursive: true });

    writeJson(join(dir, 'swarm_state.json'), {
      schema_version: '1.0',
      current_phase: 'INIT',
      next_phase: 'ARCHITECT',
      is_locked: false,
      required_phase_sequence: [
        'ARCHITECT',
        'QA_CONTRACT',
        'BACKEND',
        'ANALYST_CI_GATE',
        'FRONTEND',
        'QA_E2E',
        'ANALYST_FINAL',
      ],
      history: [],
    });

    git(dir, ['init']);
    git(dir, ['add', 'swarm', 'swarm_state.json']);
    git(dir, ['-c', 'user.name=CI', '-c', 'user.email=ci@example.com', 'commit', '-m', 'base']);
    const baseSha = git(dir, ['rev-parse', 'HEAD']);

    mkdirSync(join(dir, 'docs'), { recursive: true });
    writeFileSync(join(dir, 'docs', 'note.md'), '# note\n', 'utf-8');
    git(dir, ['add', 'docs/note.md']);
    git(dir, ['-c', 'user.name=CI', '-c', 'user.email=ci@example.com', 'commit', '-m', 'docs change']);
    const headSha = git(dir, ['rev-parse', 'HEAD']);

    const res = runOk('python3', ['-m', 'swarm.policy_guard', '--base', baseSha, '--head', headSha, '--json'], dir);
    const payload = JSON.parse(res.stdout) as { ok: boolean };
    expect(payload.ok).toBe(true);
  });
});
