
const path = require('path');
const Metatab = require('../metatab.js');
const assert = require('assert');
const fs = require('fs');
const flatten = require('./flatten.js');

function testData(v){
    return path.join(path.dirname(path.dirname(path.dirname(__filename))), 'test-data',v);
}

function dumpTerms(ti){
    for(var i = 0; i < ti.parsedTerms.length; i++){
        for(var j = 0; j < ti.parsedTerms[i].length; j++){
            console.log(ti.parsedTerms[i][j].toString());
        }
    }
}

var csv_url = 'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/python/test/data/children.csv';


var ti = new Metatab.TermInterpreter( testData('issue1.csv'))
var obj = JSON.parse(fs.readFileSync(testData('json/issue1.json'), 'utf8'));

ti.run();

var errors = flatten.compareDict(obj, ti.toDict());
if (errors.length) console.log(errors);



