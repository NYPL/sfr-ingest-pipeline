var fs = require('fs')

var buf = fs.readFileSync('/users/michaelbenowitz/Downloads/epub30-test-0300-20170809.epub')
console.log(JSON.stringify(buf))
