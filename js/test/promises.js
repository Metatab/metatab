
var GenerateRows = require('../generaterows.js');
const path = require('path');

function testData(v){
    return path.join(path.dirname(path.dirname(path.dirname(__filename))), 'test-data',v);
}


new Promise(function(resolve, reject){
    
    console.log("Starting");
    
    GenerateRows.generate(testData('children.csv'), function(row){
        console.log("A", row);
    }, function(){
        console.log("Done");
        resolve('resolved');
    });
    
}).then(function(result){
    console.log("Really Done", result);
}).catch(function(err){
   console.log(err);
});

