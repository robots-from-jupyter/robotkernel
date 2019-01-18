"use strict";
/*
  Copyright (c) 2018 Georgia Tech Research Corporation
  Copyright (c) 2019 Asko Soukka <asko.soukka@iki.fi>
  Distributed under the terms of the BSD-3-Clause License
*/
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
Object.defineProperty(exports, "__esModule", { value: true });
/*
  An implementation of syntax highlighting for robot framework 3.1.

  http://robotframework.org/robotframework/3.1/RobotFrameworkUserGuide.html

  When necessary, the source code is consulted and ultimately trusted:

  https://github.com/robotframework/robotframework
*/
// tslint:disable-next-line
/// <reference path="../typings/codemirror/codemirror.d.ts"/>
// tslint:disable-next-line
require("codemirror/addon/mode/simple");
var CodeMirror = require("codemirror");
/** helper function for compactly representing a rule */
function r(regex, token, opt) {
    return __assign({ regex: regex, token: token }, opt);
}
/** Possible Robot Framework table names. Group count is important.  */
var TABLE_NAMES = {
    keywords: /(\|\s)?(\*+\s*)(user keywords?|keywords?)(\s*\**)/i,
    settings: /(\|\s)?(\*+\s*)(settings?)(\s*\**)/i,
    test_cases: /(\|\s)?(\*+\s*)(tasks?|test cases?)(\s*\**)/i,
    variables: /(\|\s)?(\*+\s*)(variables?)(\s*\**)/i
};
/** Enumerate the possible rules  */
var RULES_TABLE = Object.keys(TABLE_NAMES).map(function (next) {
    return r(TABLE_NAMES[next], ['bracket', 'header', 'header', 'header'], {
        next: next,
        sol: true
    });
});
/** Pattern to match the start of a variable */
var VAR_START = /[\$&@%]\{/;
/** Pattern to match the end of a variable */
var VAR_END = /\}/;
/** Valid python operators */
var VAR_OP = /[*\-+\\%&|=><!]/;
/** Valid python numbers */
var VAR_NUM = /0(b[01]+|o[0-7]+|x[0-9a-f]+)|(\d+)(\.\d+)?(e-?(\d+)(\.\d+)?)?/i;
/**
    Valid python builtins
    Valid  way out at the end is a lookahead for VAR_OP, end or .
*/
var VAR_BUILTIN = /(none|(cur|temp|exec)dir|\/|:|\\n|true|empty|false|null|space|test (name|documentation|status|message|tags)|prev test (name|status|message)|suite (name|source|documentation|status|message|metadata)|keyword (status|message)|(report|debug) file|log (file|level)|output (dir|file))(?=[.}]|\s+[*\-+\\%&|=><!])/i;
/** a rule for the beginning of the variable state */
var RULE_VAR_START = r(VAR_START, 'variable', { push: 'variable' });
/** a rule for the end of the variable state */
var RULE_VAR_END = r(VAR_END, 'variable');
/** a rule for a number */
var RULE_NUM = r(VAR_NUM, 'number');
/** a rule for starting a single quote */
var RULE_SINGLE_STRING_START = r(/'/, 'string', { push: 'single_string' });
/** a rule for starting a double quote */
var RULE_DOUBLE_STRING_START = r(/"/, 'string', { push: 'double_string' });
/** a rule for capturing tags (and friends) in keyword/test/task definitions */
var RULE_TAGS = r(/([| ]* *)(\[\s*)(tags)(\s*\])( *\|?)/i, ['bracket', 'atom', 'atom', 'atom', 'bracket'], { sol: true, push: 'tags' });
/** rule for special case of applying tags at the suite level */
var RULE_SUITE_TAGS = r(/(force tags|default tags)(  +)/i, ['atom', null], {
    push: 'tags',
    sol: true
});
/** rule for special case of applying tags at the suite level (with pipes) */
var RULE_SUITE_TAGS_PIPE = r(/(\| +)(force tags|default tags)( *\|?)/i, ['bracket', 'atom', 'bracket'], { sol: true, push: 'tags' });
/** rule for bracketed settings of keyword/test/task */
var RULE_SETTING_KEYWORD = r(/([| ]* *)(\[\s*)(setup|teardown|template)(\s*\])( *\|?)/i, ['bracket', 'atom', 'atom', 'atom', 'bracket'], { push: 'keyword_invocation', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword */
var RULE_SUITE_SETTING_KEYWORD = r(/(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)(  +)/i, ['atom', null], { push: 'keyword_invocation', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword (with pipes) */
var RULE_SUITE_SETTING_KEYWORD_PIPE = r(/(\| +)(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)( +\|)/i, ['bracket', 'atom', 'bracket'], { push: 'keyword_invocation', sol: true });
/** collects the states that we build */
var states = {};
/** base isn't a state. these are the "normal business" that any state might use */
var base = RULES_TABLE.concat([
    RULE_VAR_START,
    RULE_VAR_END,
    r(/\|/, 'bracket'),
    r(/[\.]{3}/, 'bracket'),
    r(/#.*$/, 'comment'),
    r(/\\ +/, 'bracket'),
    r(/\\(?=$)/, 'bracket'),
    r(/([^ =]*)(=)/, ['attribute', 'operator']),
    r(/_\*.*?\*_/, 'string.strong.em'),
    r(/\*.*?\*/, 'string.strong'),
    r(/\_.*?\_/, 'string.em'),
    // this is pretty extreme, but seems to work
    r(/[^ \$]+/, 'string')
]);
/** the starting state (begining of a file) */
states.start = [
    r(/(%%python)( module )?(.*)?/, ['meta', 'keyword', 'variable'], {
        mode: { spec: 'ipython' },
        sol: true
    }),
    r(/(%%[^ ]*).*$/, 'meta', { sol: true })
].concat(base);
/** settings states */
states.settings = [
    RULE_SUITE_TAGS_PIPE,
    RULE_SUITE_TAGS,
    RULE_SUITE_SETTING_KEYWORD_PIPE,
    RULE_SUITE_SETTING_KEYWORD,
    r(/(\|* *)(library|resource|variables|documentation|metadata|test timeout|task timeout)( *)/i, ['bracket', 'atom', null], { sol: true })
].concat(base);
/** pattern for starting keywords */
var KEY_START = /(  +)/;
/** pattern for starting keywords (with pipes) */
var KEY_START_PIPE = /(\| *\|)( +)/;
/** pattern for starting behavior-driven-development keywords */
var KEY_BDD_START = /(\| *\| *|  +)?(given|when|then|and|but)/i;
/** rule for behavior-driven-development keywords */
var RULE_START_BDD = r(KEY_BDD_START, ['bracket', 'builtin.em'], {
    push: 'keyword_invocation',
    sol: true
});
/** rule for whitespace keywords */
var RULE_KEY_START = r(KEY_START, null, {
    push: 'keyword_invocation',
    sol: true
});
/** rule for pipe keywords */
var RULE_KEY_START_PIPE = r(KEY_START_PIPE, ['bracket', null], {
    push: 'keyword_invocation',
    sol: true
});
/** rules for capturing individual tags */
states.tags = [
    r(/ \| */, 'bracket'),
    r(/^($|\n)/, null, { pop: true }),
    RULE_VAR_START,
    r(/\}(?=$)/, 'variable', { pop: true }),
    RULE_VAR_END,
    r(/^ *(?=$)/, null, { pop: true }),
    r(/ +/, null),
    r(/[^\$&%@]*?(?=(  +| \|))/, 'tag'),
    r(/[^\$&%@]*?(?= *\|?$)/, 'tag', { pop: true }),
    // fall back to single char
    r(/[^\$&%@|]/, 'tag')
];
/** rules for data rows inside a keyword definition */
states.keywords = [
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    r(/([\| ]* *)(\[\s*)(arguments|documentation|return|timeout)(\s*\])( *\|?)/i, ['bracket', 'atom', 'atom', 'atom', 'bracket'], { sol: true }),
    RULE_START_BDD,
    RULE_KEY_START_PIPE,
    RULE_KEY_START,
    r(/\| (?=[^ ]*\|)/, null, { sol: true, push: 'keyword_invocation' }),
    r(/(?=[^ ])/, null, { sol: true, push: 'keyword_invocation' })
].concat(base);
/** rules for data rows inside test/task definition */
states.test_cases = [
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    r(/([\| ]* *)(\[\s*)(documentation|timeout)(\s*\])/i, ['bracket', 'atom', 'atom', 'atom'], { sol: true }),
    RULE_START_BDD,
    RULE_KEY_START_PIPE,
    RULE_KEY_START,
    r(/(\| +)([^ *\|\.][^\|]*?)( *)(\|?$)/, ['bracket', 'string.header', 'bracket'], {
        sol: true
    }),
    r(/(\| +)(.+?)( \| )/, ['bracket', 'string.header', 'bracket'], {
        sol: true
    }),
    r(/([^| *].+$)/, 'string.header', { sol: true })
].concat(base);
/** rules for inside of an invoked keyword instance */
states.keyword_invocation = [
    r(/^(?= *$)/, null, { pop: true }),
    RULE_VAR_START,
    r(/\}(?=$)/, 'variable', { pop: true }),
    RULE_VAR_END,
    r(/#.*$/, 'comment', { pop: true }),
    r(/( \| |  +)/, 'bracket', { pop: true }),
    r(/ ?=(  +)/, 'operator'),
    r(/(\\|[\.]{3}) +/, 'bracket', { pop: true }),
    r(/ /, null),
    r(/([^ ]*?(?=[\$&%@]\{))/i, 'keyword'),
    r(/[^ \|]+(?=$|[|])/, 'keyword', { pop: true }),
    r(/([^\n\$ *=\|]+?(?= ))/i, 'keyword')
].concat(base);
/** curious rule for the variables table */
states.variables = base.slice();
/** rules for inside of a variable reference */
states.variable = [
    RULE_VAR_START,
    r(VAR_BUILTIN, 'builtin'),
    RULE_NUM,
    r(VAR_OP, 'operator'),
    r(/\./, 'operator', { push: 'variable_property' }),
    r(/\[/, 'bracket', { next: 'variable_index' }),
    r(/\}(?=\[)/, 'variable'),
    r(/[^}\n$]/, 'variable'),
    r(/^(?=\})/, 'variable', { pop: true })
];
/** rules for extended syntax in a variable reference */
states.variable_property = [
    RULE_VAR_START,
    RULE_VAR_END,
    RULE_NUM,
    RULE_SINGLE_STRING_START,
    RULE_DOUBLE_STRING_START,
    r(VAR_OP, 'operator'),
    r(/\(/, 'bracket'),
    r(/\)/, 'bracket', { pop: true }),
    r(/([a-z_][a-z_\d]*)(=)/i, ['variable', 'operator']),
    r(/,/, 'punctuation'),
    r(/[^}](?=\})/, 'property', { pop: true }),
    r(/(^\})( *(?=$|\n))/, ['bracket', null], { pop: true }),
    r(/^ *(?=$|\n)/, null, { pop: true }),
    r(/[^}]/, 'property')
];
/** rules for strings with single quotes */
states.single_string = [
    r(/\\'/, 'string'),
    r(/'/, 'string', { pop: true }),
    r(/./, 'string')
];
/** rules for strings with double quotes */
states.double_string = [
    r(/\\"/, 'string'),
    r(/"/, 'string', { pop: true }),
    r(/./, 'string')
];
/** rules for square-bracketed index referencing */
states.variable_index = [
    RULE_VAR_START,
    RULE_VAR_END,
    RULE_NUM,
    r(/\[/, 'bracket'),
    r(/\](?=\])/, 'bracket'),
    r(/(\])(\})( ?=?)/, ['bracket', 'variable', 'operator'], { pop: true }),
    r(/(\])(\[)/, 'bracket'),
    r(/\]/, 'bracket', { pop: true }),
    r(/[^\]]/, 'string')
];
/** well-known mime type for robot framework (pygments, etc.) */
exports.MIME_TYPE = 'text/x-robotframework';
/** the canonical CodeMirror mode name */
exports.MODE_NAME = 'robotframework';
/** the human-readable name of the CodeMirror mode */
exports.MODE_LABEL = 'robotframework';
/** primary file extension */
exports.DEFAULT_EXTENSION = 'robot';
/** all recognized file extensions */
exports.EXTENSIONS = [exports.DEFAULT_EXTENSION, 'resource'];
/** the actual exported function that will install the mode in CodeMirror */
function defineRobotMode() {
    var _CodeMirror = CodeMirror;
    _CodeMirror.defineSimpleMode(exports.MODE_NAME, __assign({ meta: {
            dontIndentStates: ['comment'],
            lineComment: '#'
        } }, states));
    CodeMirror.defineMIME(exports.MIME_TYPE, exports.MODE_NAME);
    CodeMirror.modeInfo.push({
        ext: exports.EXTENSIONS,
        mime: exports.MIME_TYPE,
        mode: exports.MODE_NAME,
        name: exports.MODE_LABEL
    });
}
exports.defineRobotMode = defineRobotMode;
/** install the mode */
defineRobotMode();
