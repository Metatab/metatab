
const path = require('path');
const Metatab = require('../metatab.js');
const assert = require('assert');
const fs = require('fs');
const flatten = require('./flatten.js');

function testData(v){
    return path.join(path.dirname(path.dirname(path.dirname(__filename))), 'test-data',v);
}

var csv_url = 'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/python/test/data/children.csv';

if (false){
    var GenerateRows = require('../generaterows.js');
    
    GenerateRows.generate('./children.csv', function(row){
        console.log("A", row);
    });
    
    GenerateRows.generate(csv_url, function(row){
        console.log("B", row);
    });
    

    for ( var term of  Metatab.parseTerms(testData('children.csv'))){
        console.log(term.toString());
    }
 
}

var ti = new Metatab.TermInterpreter( testData('example1.csv'))
var obj = JSON.parse(fs.readFileSync(testData('json/example1.json'), 'utf8'));

ti.run();

var errors = flatten.compareDict(ti.toDict(), obj);
if (errors.length) console.log(errors);
