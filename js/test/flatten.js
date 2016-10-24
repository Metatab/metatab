

(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define([], factory);
    }
    else if (typeof exports === 'object') {
        // CommonJS
        module.exports = factory();
    }
    else {
        // Browser globals (Note: root is window)
        root.returnExports = factory();
    }
}(this, function() {
    
    // From http://jsfiddle.net/WSzec/6/
    var flatten = function(data) {
        var result = {};
        
        function recurse (cur, prop) {
            if (Object(cur) !== cur) {
                result[prop] = cur;
            } else if (Array.isArray(cur)) {
                 for(var i=0, l=cur.length; i<l; i++)
                     recurse(cur[i], prop ? prop+"."+i : ""+i);
                if (l == 0)
                    result[prop] = [];
            } else {
                var isEmpty = true;
                for (var p in cur) {
                    isEmpty = false;
                    recurse(cur[p], prop ? prop+"."+p : p);
                }
                if (isEmpty)
                    result[prop] = {};
            }
        }
        
        recurse(data, "");
        
        return result;
        
    };
    
    var compareDict = function(a,b){
        var errors = [];
    
        var fa = flatten(a);
        var fb = flatten(b);
        
        for(var k in fb){
            if (!(k in fa)){
                errors.push("Missing in a: "+k)
            }
        }
        
        for(var k in fa){
            if (!(k in fb)){
                errors.push("Missing in b: "+k)
            }
            if( fa[k] && fb[k] && fa[k] != fb[k]){
                errors.push("Different: "+k+": "+fa[k]+" <> "+fb[k]);
            }
        }
        
        return errors;
    
    };
    
    return {
      flatten: flatten,
      compareDict: compareDict,
    };
}));