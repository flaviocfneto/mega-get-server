/** @type {import('lighthouse-ci').LHCI.ServerCommandOptions} */
module.exports = {
  ci: {
    collect: {
      numberOfRuns: 1,
      url: ['http://127.0.0.1:4173/'],
      startServerCommand: 'npm run preview:ci',
      startServerReadyPattern: 'Local:',
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', {minScore: 0.88}],
        'categories:best-practices': ['warn', {minScore: 0.75}],
        'categories:performance': ['warn', {minScore: 0.45}],
      },
    },
  },
};
