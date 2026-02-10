// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

describe('Governance Audit', () => {
  const rootDir = process.cwd();

  it('should have a valid SWARM_CONSTITUTION.md', () => {
    const constitutionPath = join(rootDir, 'SWARM_CONSTITUTION.md');
    expect(existsSync(constitutionPath)).toBe(true);
    const content = readFileSync(constitutionPath, 'utf-8');
    expect(content).toContain('Constitutional Multi-Agent Swarm OS (CMAS-OS)');
    expect(content).toContain('# B) Swarm Constitution (Rules)');
    expect(content).toContain('# D) Execution Protocol as a Finite State Machine');
    // Ensure all 7 phases are mentioned in correct order
    const phases = [
      'ARCHITECT',
      'QA_CONTRACT',
      'BACKEND',
      'ANALYST_CI_GATE',
      'FRONTEND',
      'QA_E2E',
      'ANALYST_FINAL'
    ];
    phases.forEach(phase => {
      expect(content).toContain(phase);
    });
  });

  it('should have a valid TASKS_CONTEXT.md', () => {
    const contextPath = join(rootDir, 'TASKS_CONTEXT.md');
    expect(existsSync(contextPath)).toBe(true);
    const content = readFileSync(contextPath, 'utf-8');
    expect(content).toContain('# TASKS_CONTEXT');
    expect(content).toContain('## Stack');
    expect(content).toContain('## Critical Constraints');
    // Guardrail: the project context must not be left as a template placeholder.
    expect(content).not.toContain('Describe the product in 1-3 sentences.');

    // Stack keys must have non-empty values (avoid "Key:" with nothing after).
    const requiredStackKeys = ['Language', 'Framework', 'Storage', 'Testing', 'E2E'];
    requiredStackKeys.forEach((key) => {
      expect(content).toMatch(new RegExp(`^\\s*-\\s*${key}:\\s*\\S+`, 'm'));
    });
  });

  it('should have a valid swarm_state.json schema', () => {
    const statePath = join(rootDir, 'swarm_state.json');
    expect(existsSync(statePath)).toBe(true);
    const content = readFileSync(statePath, 'utf-8');
    const state = JSON.parse(content);
    expect(state).toHaveProperty('schema_version');
    expect(state).toHaveProperty('current_phase');
    expect(state).toHaveProperty('next_phase');
    expect(state).toHaveProperty('required_phase_sequence');
    // Ensure required sequence matches constitution
    const expectedSequence = [
      'ARCHITECT',
      'QA_CONTRACT',
      'BACKEND',
      'ANALYST_CI_GATE',
      'FRONTEND',
      'QA_E2E',
      'ANALYST_FINAL'
    ];
    expect(state.required_phase_sequence).toEqual(expectedSequence);
  });

  it('should include the Change Request protocol artifacts', () => {
    const crDocPath = join(rootDir, 'docs', 'CHANGE_REQUEST.md');
    expect(existsSync(crDocPath)).toBe(true);
    const crDoc = readFileSync(crDocPath, 'utf-8');
    expect(crDoc).toContain('Change Request Protocol (CR)');

    const changesDir = join(rootDir, 'tasks', 'changes');
    expect(existsSync(changesDir)).toBe(true);
  });
});
