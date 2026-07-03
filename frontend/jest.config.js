// Minimal Jest config — added in Phase 1a Day 2 to enable frontend unit tests
// (the repo had the devDeps: jest, ts-jest, jest-environment-jsdom,
// @testing-library/react — but no config, so `jest --passWithNoTests` never
// ran anything). Scoped to what the useVisionEvents hook test needs:
// ts-jest transform (forced to CommonJS so Jest can run it), jsdom env for
// React, and the "@/" path alias from tsconfig.
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  transform: {
    '^.+\\.(ts|tsx)$': [
      'ts-jest',
      { tsconfig: { module: 'commonjs', jsx: 'react-jsx', esModuleInterop: true } },
    ],
  },
  testMatch: ['<rootDir>/src/**/__tests__/**/*.test.(ts|tsx)'],
};
