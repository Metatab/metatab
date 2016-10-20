/*!
	Metatab For Javascript
	v0.0.1
	https://github.com/CivicKnowledge/metatab
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

    const ELIDED_TERM = '<elided_term>';
    const NO_TERM = '<no_term>';

    var parentTerm;
    var recordTerm;

    var splitTerm = function(term){
        
        if ( term.indexOf(".") >= 0 ){
            var parts = term.split(".");
            parentTerm = parts[0].trim();
            recordTerm = parts[1].trim();
        
            if (parentTerm == ''){
                parentTerm = ELIDED_TERM;
            }

        } else {
            parentTerm = NO_TERM;
            recordTerm = term.trim()
         
        }

        return [parentTerm, recordTerm];
    };
    
    var splitTermLower = function(term){
        var terms = splitTerm(term);
        return [terms[0].toLowerCase(), terms[1].toLowerCase()];
    };
    

    var Term = function (term, value, termArgs) {
        this.term = term;
        var p =  splitTermLower(this.term);
        this.parentTerm = p[0];
        this.recordTerm = p[1];
        
        this.value = value.trim();
        
        if (Array.isArray(termArgs)){
            this.termArgs = []
            var valid_vals = 0
            for (var i=0; i < termArgs.length; i++){
                if (termArgs[i].trim()){
                    valid_vals++;
                }
                this.termArgs.push(termArgs[i].trim());
            }
            
            if (valid_vals == 0){
                this.termArgs = [];
            }
            
        } else {
            this.termArgs = [];
        }
        
        this.children = [];
        
        this.section = null;
        this.fileName = null;
        this.row = null;
        this.col = null;
        
        this.termValueName = '@value';  

        this.childPropertyType  = 'any';
        this.valid = null;

        this.isArgChild= null;
        
        this.toString = function(){
            return "<Term "+this.parentTerm+"."+this.recordTerm+"="+
            this.value+" "+JSON.stringify(this.termArgs)+" >"
        }
        
        this.clone = function(){
            
            var c = new Term(this.term, this.value, this.termArgs);
            c.parentTerm = this.parentTerm;
            c.recordTerm = this.recordTerm;
            c.children = this.children;
            c.section = this.cection;
            c.filename = this.filename;
            c.row = this.row;
            c.col = this.col;
            c.termValueName = this.termValueName;
            c.childPropertyType = this.childPropertyType;
            c.valid = this.valid;
            c.isArgChild = this.isArgChild;
            
            return c;
            
        }

    };

    var termFromRow = function(row){
        try {
            return new Term(row[0], row[1], row.slice(2));
        }  catch (e) {
            return null
            
        } 
        
         
    };

    var generateRows = function (path, cb) {
       
        var fs = require('fs')
        fs.readFile(path, 'utf8', function (err,data) {
          if (err) {
            return console.log(err);
          }
          
          var pr = Papa.parse(data);
          
          // TODO: Handle errors in rows
          
          for(var i = 0; i < pr['data'].length; i++){
              cb(i, pr['data'][i]);
          }
              
        });
    };
    
    var generateTerms = function(path, cb){
        
        generateRows(path, function(rowNum, row){
            var term = termFromRow(row);
            if (term && term.term ){
                term.row = rowNum;
                term.col = 1;
                term.fileName = path;
                cb(term);
                
                // Include another file
                if (term.recordTerm.toLowerCase() != 'include' ){
                    // Do includy stuff
                }
                
                // Generate child terms
                if (term.recordTerm.toLowerCase() != 'section' ){
                    for(var i = 0; i < term.termArgs.length; i++){
                        if (term.value.trim()){
                            var childTerm = 
                                new Term(term.recordTerm.toLowerCase()+"."+String(i), 
                                         String(term.termArgs[i]), 
                                         [] );
                            childTerm.row = rowNum;
                            childTerm.col = i + 2;
                            childTerm.fileName = path;
                            cb(childTerm);
                        }
                    }
                }
                
            } else {
                // TODO Handle error
            }
        });
    }
    
    var TermInterpreter = function (path, cb) {
      
        this.terms = {};
        this.sections = {};
        this.errors = [];
      
        this.substituteSynonym = function(nt, t){
            
        }
        
        this.join = function(t1, t2){
            return t1+'.'+t2
        }
    
        this.installDeclareTerms = function(){
            
            var declareTerms = {
                NO_TERM + '.section': {'termvaluename': 'name'},
                NO_TERM + '.synonym': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
                NO_TERM + '.declareterm': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
                NO_TERM + '.declaresection': {'termvaluename': 'section_name', 'childpropertytype': 'sequence'},
                NO_TERM + '.declarevalueset': {'termvaluename': 'name', 'childpropertytype': 'sequence'},
                'declarevalueset.value': {'termvaluename': 'value', 'childpropertytype': 'sequence'},
            };
        
        }
    
        this.run = function(){
        
            var self = this;
            
            var lastParentTerm = 'root';
            var paramMap = {};
        
            generateTerms(path, function(term){
            
                var nt = term.clone();
            
                self.substituteSynonym(nt, term);
            
                
                if (nt.parentTerm == ELIDED_TERM && lastParentTerm){
                    // If the parent term was elided -- the term starts with '.'
                    // then substitute in the last parent term
                    nt.parentTerm = lastParentTerm;
                } else if ( ! nt.isArgChild){
                    // If the parent term was not elided, and the term is
                    // in Column A of the spreadsheet ( rather than a child term 
                    // in the term arg list, Col C+), then we can use it for the 
                    // last parent term. 
                    lastParentTerm = nt.recordTerm;
                }
            
                if (parseInt(term.recordTerm) in paramMap){
                    // Convert child terms from the args, which are initially 
                    // given recordTerm names of integers, according to their 
                    // position in the arg list. 
                    nt.recordTerm = String(paramMap[parseInt(term.recordTerm)]);
                }
                
                
                if (nt.recordTerm.toLowerCase() == 'section'){
                    // Section terms set the param map
                    paramMap = {};
                    for(var i = 0; i < nt.termArgs.length; i++){
                        paramMap[i] = String(nt.termArgs[i]).toLowerCase();
                    }
                    
                    return;
                }
                
                if (nt.recordTerm.toLowerCase() == 'declare'){
                    var fn;
                    if(nt.value.startswith('http'){
                        fn = nt.value.replace(/\/$/, "");
                    } else {
                        fn = join(dirname(t.file_name), t.value.replace(/\/$/, "");
                    }
                }
                
            
                cb(nt);
            });
        };
        
        
        
    };
    
    
    var parse = function(path){
        
        var interp = new TermInterpreter(path, function(term){
            console.log(term.toString()); 
        });
        
        console.log(interp);
        
        interp.run();
                
    }
    
    return {
      generateRows: generateRows,
      parse: parse
    };
}));

