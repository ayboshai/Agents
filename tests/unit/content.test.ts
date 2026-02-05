import { describe, expect, it } from 'vitest';
import { companyData } from '../../data/content';

describe('content contract: company contacts integrity', () => {
  it('test_positive_flow: exposes exact AB-Company contact constants', () => {
    expect(companyData.companyName).toBe('AB-Company');
    expect(companyData.phone).toBe('+79659903160');
    expect(companyData.email).toBe('ticketbad@gmail.com');
  });

  it('test_edge_cases: whatsappUrl is wa.me-compatible and normalized', () => {
    expect(companyData.whatsappUrl).toBe('https://wa.me/79659903160');
    expect(companyData.whatsappUrl).toMatch(/^https:\/\/wa\.me\/\d+$/);
  });

  it('test_security: rejects malformed protocol and script injection vectors in url', () => {
    expect(companyData.whatsappUrl.toLowerCase()).not.toContain('javascript:');
    expect(companyData.whatsappUrl.toLowerCase()).not.toContain('<script');
  });
});
