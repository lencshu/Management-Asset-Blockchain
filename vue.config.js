// const IS_PRODUCTION = process.env.NODE_ENV === 'production'
// var HtmlWebpackPlugin = require('html-webpack-plugin')
// var HtmlWebpackInlineSourcePlugin = require('html-webpack-inline-source-plugin')
module.exports = {
  outputDir: 'backend/dists',
  assetsDir: 'static',
  // baseUrl: IS_PRODUCTION
  // ? 'http://cdn123.com'
  // : '/',
  // For Production, replace set baseUrl to CDN
  // And set the CDN origin to `yourdomain.com/static`
  // Whitenoise will serve once to CDN which will then cache
  // and distribute
  // pages: {
  //   index: {
  //     entry: 'frontend/main.js'
  //   }
  // },
  devServer: {
    proxy: {
      '/api*': {
        // Forward frontend dev server request for /api to django dev server
        target: 'http://localhost:8081',
        changeOrigin: true,
        secure: false
      }
    }
  }
  // /mnt/c/Users/lencs/Desktop/proj/_exchangeRe/_decompose/pyReform/dists/index.html
  // css: {
  //   extract: false,
  // },
  // configureWebpack: {
  //   optimization: {
  //     splitChunks: false // makes there only be 1 js file - leftover from earlier attempts but doesn't hurt
  //   },
  //   plugins: [
  //     new HtmlWebpackPlugin({
  //       inlineSource: '.(js|css)$', // embed all javascript and css inline
  //       // inject: true
  //       // template: "./dists/index.html"
  //     }),
  //     new HtmlWebpackInlineSourcePlugin()
  //   ]
  // }
}
