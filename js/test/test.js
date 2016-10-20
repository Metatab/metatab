
var csv_url = 'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/python/test/data/children.csv';

if (false){
    var GenerateRows = require('../generaterows.js');
    
    GenerateRows.generate('./children.csv', function(row){
        console.log("A", row);
    });
    
    GenerateRows.generate(csv_url, function(row){
        console.log("B", row);
    });
}


var Metatab = require('../metatab.js');


//Metatab.parse('./children.csv');
Metatab.parse(csv_url);