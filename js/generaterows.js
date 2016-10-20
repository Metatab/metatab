/* 
 Row Generators. Read a URL and generate row data 
*/


(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define(['papaparse'], factory);
    } else if (typeof exports === 'object') {
        // CommonJS
        module.exports = factory(require('papaparse') );
    } else {
        // Browser globals (Note: root is window)
        root.returnExports = factory(root.Papa );
    }
}(this, function (Papa) {
    
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
    
    var generateRows = function (ref, cb) {
        
        // Based on the value of ref and the environment, return a row generator
        if (isNode()){
            if(ref.startsWith('http:') || ref.startWith('https:')){
                Papa.parse(ref, {
                	download: true,
                	worker: true,
                	step: function(row) {
                		cb(row.data);
                	},
                	complete: function() {
                		//
                	}
                });
            } else {
                // Assume local filesystem
                 require('fs').readFile(path, 'utf8', function (err,data) {
                    if (err) {
                        console.log(err);
                        return;
                    }
                
                    var pr = Papa.parse(data,{
                        worker: true,
                        step: function(row) {
                		    cb(row.data);
                	    },
                	    complete: function() {
                		    //
                	    }
                    });
                });   
            }
        } else if (isBrowser()){
            if(ref.startsWith('http:') || ref.startWith('https:')){
                
            } else {
                throw GenerationError(
                    "In browser, can only fetch via http/https");
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
      generateRows: generateRows,


    };
})