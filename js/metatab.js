/*!
	Metatab For Javascript
	v0.0.1
	https://github.com/CivicKnowledge/metatab
*/

"use strict";

function dirname(path) {
    return path.replace(/\\/g, '/').replace(/\/[^\/]*$/, '');
}

(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define(['generaterows'], factory);
    }
    else if (typeof exports === 'object') {
        // CommonJS
        module.exports = factory(require('./generaterows'));
    }
    else {
        // Browser globals (Note: root is window)
        root.returnExports = factory(root.GenerateRows);
    }
}(this, function(GenerateRows) {

    const ELIDED_TERM = '<elided_term>';
    const ROOT_TERM = 'root';

    var normalizeTerm = function(term) {
        var parts = splitTermLower(term);
        return parts[0] + '.' + parts[1];
    }

    var splitTerm = function(term) {

        var parentTerm;
        var recordTerm;

        if (term.indexOf(".") >= 0) {
            var parts = term.split(".");
            parentTerm = parts[0].trim();
            recordTerm = parts[1].trim();

            if (parentTerm == '') {
                parentTerm = ELIDED_TERM;
            }

        }
        else {
            parentTerm = ROOT_TERM;
            recordTerm = term.trim()

        }

        return [parentTerm, recordTerm];
    };

    var splitTermLower = function(term) {
        var terms = splitTerm(term);
        return [terms[0].toLowerCase(), terms[1].toLowerCase()];
    };

    var Term = function(term, value, termArgs, rowN, colN, fileName) {
        this.term = term;
        this.row = rowN;
        this.col = colN;
        this.fileName = fileName;

        this.value = value && value.trim();

        var p = splitTermLower(this.term);
        this.parentTerm = p[0];
        this.recordTerm = p[1];

        if (Array.isArray(termArgs)) {
            this.termArgs = []
            var valid_vals = 0
            for (var i = 0; i < termArgs.length; i++) {
                if (termArgs[i].trim()) {
                    valid_vals++;
                }
                this.termArgs.push(termArgs[i].trim());
            }

            if (valid_vals == 0) {
                this.termArgs = [];
            }

        }
        else {
            this.termArgs = [];
        }

        this.children = [];

        this.section = null;

        this.termValueName = '@value';

        this.childPropertyType = 'any';
        this.valid = Boolean(term) && Boolean(this.recordTerm);

        this.isArgChild = null;

        this.canBeParent = (!this.isChidArg && this.parentTerm != ELIDED_TERM);

        this.toString = function() {

            var fn;
            if (this.fileName) {
                var fileParts = this.fileName.split("/");
                fn = fileParts.pop();
            }
            else {
                fn = '<null>';
            }

            return "<Term " + fn + " " + this.row + ":" + this.col + " " +
                this.parentTerm + "." + this.recordTerm + "=" +
                this.value + " " + JSON.stringify(this.termArgs) +
                " >"
        }

        this.clone = function() {

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
            c.canBeParent = this.canBeParent;

            return c;

        }

        this.joinedTerm = function() {
            return this.parentTerm + '.' + this.recordTerm;
        }

        this.joinedTermLc = function() {
            return this.parentTerm.toLowerCase() + '.' +
                this.recordTerm.toLowerCase();
        }

        this.termIs = function(v) {
            if (this.recordTerm.toLowerCase() == v.toLowerCase() ||
                this.joinedTermLc() == v.toLowerCase() ||
                this.recordTerm.toLowerCase().indexOf('.' + v.toLowerCase()) > -1
            ) {
                return true;
            }
            else {
                return false;
            }
        }

        // Return child terms created from the row args. 
        this.argChildren = function() {

            if (this.termIs('section')) {
                return [];
            }

            var childTerms = [];

            for (var j = 0; j < this.termArgs.length; j++) {
                childTerms.push(
                    new Term(this.recordTerm.toLowerCase() + "." + String(j),
                        String(this.termArgs[j]), [], i, j + 2, this.fileName));
            }

            return childTerms;
        }


    };

    var generateTerms = function(path, cb) {


        if (!cb) {
            cb = function(term) {
                terms.push(term);
            }
        }

        var terms = [];
        var rows = GenerateRows.generateSync(path);
        var i = 0;

        for (var row of rows['data']) {

            var term = new Term(row[0], row[1], row.slice(2), ++i, 1, path);

            if (term.valid) {

                cb(term);

                for (var child of term.argChildren()) {
                    if (child.valid && child.value) {
                        cb(child);
                    }
                }

                if (term.termIs('include')) {
                    for (var includedTerm of generateTerms(term.value)) {
                        cb(includedTerm);

                    }
                }
            }
        }

        return terms;

    }

    var TermInterpreter = function(path) {

        this.terms = {}; // Terms info from a declare doc
        this.sections = {}; // sections info from a declare doc
        this.errors = []; // Parse errors. 
        this.path = path; //  Filesystem path or URL to document
        this.declareDocs = [] // Dict tress loaded to importDeclareDoc
        this.rootTerm = null; // The Root terms, top of the link terms heirarchy
        this.parsedTerms = []; // All of the parsed terms, as an array or arrays. 
        

        this.substituteSynonym = function(nt) {
            var jtlc = nt.joinedTermLc();
            
            if ( jtlc in this.terms && 'synonym' in this.terms[jtlc]){
                    
                var syn = this.terms[jtlc]['synonym'];
                var parts = splitTermLower(syn);
                
                nt.parentTerm = parts[0];
                nt.recordTerm = parts[1];
            }
     
        };

        this.join = function(t1, t2) {
            return t1 + '.' + t2
        }

        this.installDeclareTerms = function() {

            this.terms['root.section'] = {
                'termvaluename': 'name'
            };
            this.terms['root.synonym'] = {
                'termvaluename': 'term_name',
                'childpropertytype': 'sequence'
            };
            this.terms['root.declareterm'] = {
                'termvaluename': 'term_name',
                'childpropertytype': 'sequence'
            };
            this.terms['root.declaresection'] = {
                'termvaluename': 'section_name',
                'childpropertytype': 'sequence'
            };
            this.terms['root.declarevalueset'] = {
                'termvaluename': 'name',
                'childpropertytype': 'sequence'
            };
            this.terms['declarevalueset.value'] = {
                'termvaluename': 'value',
                'childpropertytype': 'sequence'
            };

        }

        this.run = function() {

            var self = this;

            var lastParentTerm = 'root';
            var paramMap = [];
            self.rootTerm = null;

            var lastTermMap = new Map();
            var lastSection = null;
            var terms = [];

            for (var term of generateTerms(this.path)) {

                if (!self.rootTerm) {
                    self.rootTerm = new Term('Root', null);
                    self.rootTerm.row = 0;
                    self.rootTerm.col = 0;
                    self.rootTerm.file_name = term.file_name;
                    lastTermMap.set(ELIDED_TERM, self.rootTerm);
                    lastTermMap.set(self.rootTerm.recordTerm, self.rootTerm);

                    terms.push(self.rootTerm);

                }

                var nt = term.clone();


                nt.fileName = self.path;

                if (nt.parentTerm == ELIDED_TERM) {
                    // If the parent term was elided -- the term starts with '.'
                    // then substitute in the last parent term
                    nt.parentTerm = lastParentTerm;
                }

                self.substituteSynonym(nt);

                if (parseInt(term.recordTerm) in paramMap) {
                    // Convert child terms from the args, which are initially 
                    // given recordTerm names of integers, according to their 
                    // position in the arg list. 

                    nt.recordTerm = String(paramMap[parseInt(term.recordTerm)]) || nt.recordTerm;

                }

                if (nt.termIs('root.section')) {
                    // Section terms set the param map
                    paramMap = [];
                    for (var i = 0; i < nt.termArgs.length; i++) {
                        paramMap[i] = String(nt.termArgs[i]).toLowerCase();
                    }
                    lastParentTerm = self.rootTerm.recordTerm
                    lastSection = nt;
                    continue;
                }

                if (nt.termIs('declare')) {
                    var path;

                    if (nt.value.indexOf('http') === 0) {
                        path = nt.value.replace(/\/$/, "");
                    }
                    else {
                        path = dirname(nt.fileName) + "/" +
                            nt.value.replace(/\/$/, "");
                    }

                    var dci = new TermInterpreter(path);
                    dci.installDeclareTerms();

                    var declareTerms = dci.run();

                    this.importDeclareDoc(dci.toDict());


                }

                if (nt.joinedTerm() in self.terms) {

                    var tInfo = self.terms[nt.joinedTerm()];
                    nt.childPropertyType = tInfo['childpropertytype'] || 'any';
                    nt.termValueName = tInfo['termvaluename'] || '@value';
                }

                nt.valid = nt.joinedTermLc() in self.terms;
                nt.section = lastSection;

                if (nt.canBeParent) {
                    lastParentTerm = nt.recordTerm;
                    lastTermMap.set(ELIDED_TERM, nt);
                    lastTermMap.set(nt.recordTerm, nt);
                }

                var parent = lastTermMap.get(nt.parentTerm);
                if (parent) {
                    parent.children.push(nt);
                } else {
                    // This probably can't happen. And, if it can, it may be
                    // sensible to make the parent the root. 
                    throw "Could not find parent for " + nt.toString();
                }

                terms.push(nt); // Probably useless, if Root links to everything. 


            }

            this.parsedTerms.push(terms);

            return terms;

        };


        this.toDict = function(term) {

            function is_scalar(obj) {
                return (/string|number|boolean/).test(typeof obj);

            };

            function is_array(obj) {
                return (Object.prototype.toString.call(obj) === '[object Array]');
            }

            function _toDict(term){
                if (term.children.length) {
    
                    var d = {};
    
                    for (var c of term.children) {
    
                        if (c.childPropertyType == 'scalar') {
                            d[c.recordTerm] = _toDict(c);
    
                        }
                        else if (c.childPropertyType == 'sequence') {
                            if (c.recordTerm in d) {
                                d[c.recordTerm].push(_toDict(c));
                            }
                            else {
                                // The c.term property doesn't exist, so add a list
                                d[c.recordTerm] = [_toDict(c)];
                            }
    
                        }
                        else {
    
                            if (c.recordTerm in d) {
                                if (!is_array(d[c.recordTerm])) {
                                    //The entry exists, but is a scalar, so convert it to a list
                                    d[c.recordTerm] = [d[c.recordTerm]];
                                }
    
                                d[c.recordTerm].push(_toDict(c));
                            }
                            else {
                                // Doesn't exist, so add as a scalar
                                d[c.recordTerm] = _toDict(c);
                            }
                        }
                    }
    
    
    
                    if (term.value) {
                        d[term.termValueName] = term.value;
                    }
    
                    return d;
    
                }
                else {
                    return term.value;
                }
            }
            
            return _toDict(this.rootTerm);

        };

        this.importDeclareDoc = function(d) {

            this.declareDocs.push(d);

            if ('declaresection' in d) {
                for (var e of d['declaresection']) {
                    if (e) {

                        var args = [];

                        for (var k in e) {
                            if (e.hasOwnProperty(k)) {
                                var ki = parseInt(k);
                                if (typeof ki == 'number') {
                                    args[k] = e[k] || null;
                                }
                            }
                        }
                        this.sections[e['section_name'].toLowerCase()] = {
                            'args': args,
                            'terms': []
                        };
                    }
                }
            }

            if ('declareterm' in d) {
                for (var e of d['declareterm']) {
                    if (e) {
                        this.terms[normalizeTerm(e['term_name'])] = e;
                        var sk = e['section'].toLowerCase();

                        if ('section' in e && e['section'] && !(sk in this.sections)) {
                            this.sections[sk] = {
                                'args': [],
                                'terms': []
                            };
                        }

                        var st = this.sections[sk]['terms'];

                        if (!(e['section'] in st)) {
                            st.push(e['term_name']);
                        }
                    }
                }
            }

            if ('declarevalueset' in d) {
                for (var e of d['declarevalueset']) {
                    for (var termName in this.terms) {
                        if (this.terms.hasOwnProperty(termName) &&
                            'valueset' in this.terms[termName] &&
                            e['name'] && e['name'] == this.terms[termName]['valueset']) {
                            this.terms[termName]['valueset'] = e['value']
                        }
                    }
                }
            }


        };
    };

    var parse = function(path) {

        var interp = new TermInterpreter(path);

        return interp.run();

    }

    return {
        TermInterpreter: TermInterpreter,
        parse: parse,
        parseTerms: generateTerms
    };
}));
