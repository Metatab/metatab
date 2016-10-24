
const path = require('path');
const Metatab = require('../metatab.js');
const assert = require('assert');
const fs = require('fs');
const flatten = require('./flatten.js');

var urlbase = 'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/test-data/';


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

for (var fn of ['issue1','example1', 'example2','children']){
    var ti = new Metatab.TermInterpreter( testData(fn+'.csv'))
    var obj = JSON.parse(fs.readFileSync(testData('json/'+fn+'.json'), 'utf8'));
    
    ti.run();
    
    var errors = flatten.compareDict(obj, ti.toDict());
    if (errors.length){ 
        console.log('======= ',fn);
        console.log(errors);
        console.log('---- ');
        dumpTerms(ti);
        console.log(flatten.flatten(obj));
        console.log('---- ');
        console.log(flatten.flatten(ti.toDict()));
    } else {
        console.log("OK",fn);
    }
}





