
const path = require('path');
var Metatab = require('../metatab.js');

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

for (var term of Metatab.parse( testData('example1.csv'))){
    //console.log(term.toString());
}


