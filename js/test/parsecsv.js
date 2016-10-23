
var Papa = require('../papaparse');
const path = require('path');

function testData(v){
    return path.join(path.dirname(path.dirname(path.dirname(__filename))), 'test-data',v);
}

var ref1 = 'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/python/test/data/children.csv';
var ref2 = testData('children.csv')
var GenerateRows = require('../generaterows.js');
var rows = GenerateRows.generateSync(ref1);
console.log(rows);


