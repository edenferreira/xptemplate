XPTemplate priority=personal

XPT iife " IIFE
(function () {
    'use strict';

    `//code here^
}());

XPT lambda " Lambda
function (`arg^`` parameter...`{{^, `arg^`` parameter...`^`}}^) {
    `//code here^
}

XPT func " function
function `function_name^(`arg^`` parameter...`{{^, `arg^`` parameter...`^`}}^) {
    `//code here^
}

XPT cl " console debug
console.debug(`arg^`` parameter...`{{^, `arg^`` parameter...`^`}}^);

XPT cll " console debug with label
console.debug('`obj^:', `obj^);

XPT obmet " object method
`method_name^: `method_name^,
