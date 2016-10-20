/*!
	Metatab For Javascript
	v0.0.1
	https://github.com/CivicKnowledge/metatab
*/

function dirname(path) {
    return path.replace(/\\/g,'/').replace(/\/[^\/]*$/, '');
}

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
      // AMD
    define(['generaterows'], factory);
  } else if (typeof exports === 'object') {
      // CommonJS
    module.exports = factory(require('./generaterows') );
  } else {
    // Browser globals (Note: root is window)
    root.returnExports = factory (root.GenerateRows);
  }
}(this, function (GenerateRows) {

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
        
        this.value = value && value.trim();
        
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
        
        this.joinedTerm = function(){
            return this.parentTerm + '.' + this.recordTerm;
        }
        
        this.joinedTermLc = function(){
            return this.parentTerm.toLowerCase() + '.' +
                   this.recordTerm.toLowerCase();
        }
        
        this.termIs = function(v){
            if (this.recordTerm.toLowerCase() == v.toLowerCase()  || 
                this.joinedTermLc() == v.toLowerCase()){
                return true;
            } else {
                return false;
            }
        }
        
    };

    var termFromRow = function(row){
        try {
            return new Term(row[0], row[1], row.slice(2));
        }  catch (e) {
            return null
        } 
    };

    
    var generateTerms = function(path, cb){
        
        GenerateRows.generate(path, function(rowNum, row){

            var term = termFromRow(row);
            if (term && term.term ){
                term.row = rowNum;
                term.col = 1;
                term.fileName = path;
                cb(term);
                
                // Include another file
                if (term.termIs('include') ){
                    // Do includy stuff
                }
                
                // Generate child terms
                if (!term.termIs('section') ){
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
    
    var TermInterpreter = function (path) {
      
        this.terms = new Map();
        this.sections = new Map();
        this.errors = [];
      
        this.substituteSynonym = function(nt, t){
            
        }
        
        this.join = function(t1, t2){
            return t1+'.'+t2
        }
    
        this.installDeclareTerms = function(){

           this.terms['root.section'] = {'termvaluename': 'name'};
           this.terms['root.synonym'] = {'termvaluename': 'term_name', 'childpropertytype': 'sequence'};
           this.terms['root.declareterm'] = {'termvaluename': 'term_name', 'childpropertytype': 'sequence'};
           this.terms['root.declaresection'] = {'termvaluename': 'section_name', 'childpropertytype': 'sequence'};
           this.terms['root.declarevalueset'] = {'termvaluename': 'name', 'childpropertytype': 'sequence'};
           this.terms['declarevalueset.value']= {'termvaluename': 'value', 'childpropertytype': 'sequence'};

        }
    
        this.run = function(cb){
        
            var self = this;
            
            var lastParentTerm = 'root';
            var paramMap = [];
            var root = null;
            var lastTermMap = new Map();
        
            generateTerms(path, function(term){
            
                if ( ! root ){
                    root = new Term('Root', null);
                    root.row=0;
                    root.col=0;
                    root.file_name=term.file_name;
                    lastTermMap.set(ELIDED_TERM,root);
                    lastTermMap.set(root.recordTerm,root);
                    cb(root);
                }
            
                var nt = term.clone();
    
                if (nt.parentTerm == ELIDED_TERM){
                    // If the parent term was elided -- the term starts with '.'
                    // then substitute in the last parent term
                    nt.parentTerm = lastParentTerm;
                } else if (nt.parentTerm == NO_TERM ){
                    // If the parent term was not elided, and the term is
                    // in Column A of the spreadsheet ( rather than a child term 
                    // in the term arg list, Col C+), then we can use it for the 
                    // last parent term. 
                    nt.parentTerm = root.recordTerm;
                }
            
                self.substituteSynonym(nt, term);
            
                if (parseInt(term.recordTerm) in paramMap){
                    // Convert child terms from the args, which are initially 
                    // given recordTerm names of integers, according to their 
                    // position in the arg list. 
                    nt.recordTerm = String(paramMap[parseInt(term.recordTerm)]);
                }

                if (nt.termIs('section')){
                    // Section terms set the param map
                    paramMap = [];
                    for(var i = 0; i < nt.termArgs.length; i++){
                        paramMap[i] = String(nt.termArgs[i]).toLowerCase();
                    }
                    lastParentTerm = root.recordTerm
                    return;
                }
                

                if (nt.termIs('declare')){
                    var path;
                    if(nt.value.indexOf('http')===0){
                        path = nt.value.replace(/\/$/, "");
                    } else {
                        path = dirname(nt.file_name)+"/"+
                             nt.value.replace(/\/$/, "");
                    }
                    
                    var dci = TermInterpreter(path);
                    dci.installDeclareTerms();
                    
                   self.importDeclareDoc();
                }
                
                try {
                    nt.childPropertyType = self.terms.get(nt.joinedTerm()) 
                        .get('childpropertytype', 'any');
                } catch(e){
                    
                }

                try {
                    nt.termValueName = self.terms.get(nt.joinedTerm()) 
                        .get('termvaluename', '@value');
                } catch(e) {
                    
                }

                nt.valid =  self.terms.has(nt.joinedTermLc());
                
                cb(nt);
            });
        };
    };
    
    
    var parse = function(path, cb){
        
        var interp = new TermInterpreter(path);

        interp.run(cb);
                
    }
    
    return {
      parse: parse
    };
}));

