import {describe, expect, it} from 'vitest';
import {buildAppHash, parseAppHash} from './urlSections';

describe('urlSections', () => {
  it('parseAppHash maps sections and system terminal subpath', () => {
    expect(parseAppHash('')).toEqual({section: 'transfers', systemTab: 'log'});
    expect(parseAppHash('#/history')).toEqual({section: 'history', systemTab: 'log'});
    expect(parseAppHash('#/system')).toEqual({section: 'system', systemTab: 'log'});
    expect(parseAppHash('#/system/terminal')).toEqual({section: 'system', systemTab: 'terminal'});
    expect(parseAppHash('#/nope')).toEqual({section: 'transfers', systemTab: 'log'});
  });

  it('buildAppHash is inverse for supported routes', () => {
    expect(buildAppHash('transfers', 'log')).toBe('#/transfers');
    expect(buildAppHash('system', 'log')).toBe('#/system');
    expect(buildAppHash('system', 'terminal')).toBe('#/system/terminal');
  });
});
