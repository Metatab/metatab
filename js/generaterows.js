/* 
 Row Generators. Read a URL and generate row data. 
 
 Handles:
 * Local fioles
 * Remote Files
 * Spreadsheet data in Google Spreadsheets
 
*/

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        //console.log('AMD');
        define(['papaparse'], factory);
       
    } else if (typeof exports === 'object') {
        // CommonJS
        //console.log('CommonJS');
        // Papaparse runs in the browser, babyparse is for node. 
        module.exports = factory(require('./papaparse') );
       
    } else {
        // Browser globals (Note: root is window)
        // console.log('Browser');
        root.returnExports = factory(root.Papa );
       
    }
}(this, function (CsvParse, xhr) {
    
    /*
    Read CSV data from the local file system
    */
    
    
    function GenerationError(message) {
        this.message = message;
        // Use V8's native method if available, otherwise fallback
        if ("captureStackTrace" in Error)
            Error.captureStackTrace(this, InvalidArgumentException);
        else
            this.stack = (new Error()).stack;
    }

    GenerationError.prototype = Object.create(Error.prototype);
    GenerationError.prototype.name = "GenerationError";
    GenerationError.prototype.constructor = GenerationError;
        
    // Node and browser detection from 
    // http://stackoverflow.com/a/31090240
    var isBrowser=new Function("try {return this===window;}catch(e){ return false;}");
    var isNode=new Function("try {return this===global;}catch(e){return false;}");
    var isSpreadsheet=new Function("try { return Logger && SpreadsheetApp; return true; }catch(e){return false;}");
    
    var generateRows = function (ref, cb,finishCb) {
        
        // Based on the value of ref and the environment, return a row generator
        var rowNum = 0;
        if (isNode()){

            if(ref.indexOf('http:') === 0 || ref.indexOf('https:') === 0 ){
                
                CsvParse.parse(ref, {
                	download: true,
                	step: function(row) {
                		cb(++rowNum, row.data[0]);
                	},
                	complete: function(){
                	     finishCb();
                	}
                });
            } else {
                // Assume local filesystem
                 require('fs').readFile(ref, 'utf8', function (err,data) {
                    if (err) {
                        console.log(err);
                        return;
                    }
                
                    CsvParse.parse(data,{
                        worker: true,
                        step: function(row) {
                            cb(++rowNum,row.data[0]);
                	    },
                	    complete: function(){
                	        finishCb();
                	    }
                    });
                });   
            }
        } else if (isBrowser()){
            if  (ref instanceof File){ /*global File*/
                CsvParse.parse(ref, {
                	step: function(row) {
                		cb(++rowNum,row.data[0]);
                	},
                	complete: function(){
                	     finishCb();
                	}
                });
            } else if(ref.startsWith('http:') || ref.startsWith('https:')){
                CsvParse.parse(ref, {
                	download: true,
                	worker: true,
                	step: function(row) {
                		cb(++rowNum,row.data[0]);
                	},
                	complete: function(){
                	     finishCb();
                	}
                });
            }  else {
                throw GenerationError(
                    "In browser, can only fetch via http/https or use File() ");
            }
            
        } else if (isSpreadsheet()){
            if(ref.startsWith('http:') || ref.startWith('https:')){
                var text = UrlFetchApp.fetch(url).getContentText();
            } else if(ref.startsWith('gs:') ) {
                // gs: means 'google spreadsheet' -- get rows from a
                // remote spreadsheet, by spreadsheet id. 
                
                // The url format is: gs:<docid>#<sheetname>
                
                const remoteSheet = SpreadsheetApp.openById(docId) 
                                      .getSheetByName(sheetName);
                
            } else  {
                // Get rows from the local spreadsheet
                const  rows = SpreadsheetApp.getActiveSpreadsheet()
                    .getSheetByName(metaSheetName)
                    .getDataRange()
                    .getValues();
                    
                for(var i =0; i < aspread.length; i++){
                    cb(i, rows[i]);
                }
            }
        } else {
            throw GenerationError(
                "Can't determine environment, so don't know how to fetch data");
        } 

        
    };
    
        
    return {
      generate: generateRows,
    };
}));