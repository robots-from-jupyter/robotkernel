module.exports = {
  module: {
    rules: [
      {
        test: /pypi.*\/.*/,
        type: 'asset/resource'
      },
      {
        resourceQuery: /raw/,
        type: 'asset/source'
      }
    ]
  }
};
