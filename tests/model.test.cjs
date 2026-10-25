const assert = require('node:assert/strict');
const model = require('../InputModel.js');
assert.equal(model.label({available:true,engine:'rime',effectiveLanguage:'unknown'},false),'RIME');
assert.equal(model.label({available:true,engine:'rime',effectiveLanguage:'en'},false),'EN');
assert.equal(model.label({available:true,effectiveLanguage:'zh'},false),'中');
assert.equal(model.label({available:true,effectiveLanguage:'zh'},true),'…');
assert.equal(model.label({available:false,effectiveLanguage:'zh'},false),'!');
assert.match(model.tooltip({available:false},false,'连接超时'),/连接超时/);
console.log('Input model: unknown, language, pending and error states passed.');
