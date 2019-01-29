(function() {

"use strict";

// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

CodeMirror.defineSimpleMode = function(name, states) {
  CodeMirror.defineMode(name, function(config) {
    return CodeMirror.simpleMode(config, states);
  });
};

CodeMirror.simpleMode = function(config, states) {
  ensureState(states, "start");
  var states_ = {}, meta = states.meta || {}, hasIndentation = false;
  for (var state in states) if (state != meta && states.hasOwnProperty(state)) {
    var list = states_[state] = [], orig = states[state];
    for (var i = 0; i < orig.length; i++) {
      var data = orig[i];
      list.push(new Rule(data, states));
      if (data.indent || data.dedent) hasIndentation = true;
    }
  }
  var mode = {
    startState: function() {
      return {state: "start", pending: null,
              local: null, localState: null,
              indent: hasIndentation ? [] : null};
    },
    copyState: function(state) {
      var s = {state: state.state, pending: state.pending,
               local: state.local, localState: null,
               indent: state.indent && state.indent.slice(0)};
      if (state.localState)
        s.localState = CodeMirror.copyState(state.local.mode, state.localState);
      if (state.stack)
        s.stack = state.stack.slice(0);
      for (var pers = state.persistentStates; pers; pers = pers.next)
        s.persistentStates = {mode: pers.mode,
                              spec: pers.spec,
                              state: pers.state == state.localState ? s.localState : CodeMirror.copyState(pers.mode, pers.state),
                              next: s.persistentStates};
      return s;
    },
    token: tokenFunction(states_, config),
    innerMode: function(state) { return state.local && {mode: state.local.mode, state: state.localState}; },
    indent: indentFunction(states_, meta)
  };
  if (meta) for (var prop in meta) if (meta.hasOwnProperty(prop))
    mode[prop] = meta[prop];
  return mode;
};

function ensureState(states, name) {
  if (!states.hasOwnProperty(name))
    throw new Error("Undefined state " + name + " in simple mode");
}

function toRegex(val, caret) {
  if (!val) return /(?:)/;
  var flags = "";
  if (val instanceof RegExp) {
    if (val.ignoreCase) flags = "i";
    val = val.source;
  } else {
    val = String(val);
  }
  return new RegExp((caret === false ? "" : "^") + "(?:" + val + ")", flags);
}

function asToken(val) {
  if (!val) return null;
  if (val.apply) return val
  if (typeof val == "string") return val.replace(/\./g, " ");
  var result = [];
  for (var i = 0; i < val.length; i++)
    result.push(val[i] && val[i].replace(/\./g, " "));
  return result;
}

function Rule(data, states) {
  if (data.next || data.push) ensureState(states, data.next || data.push);
  this.regex = toRegex(data.regex);
  this.token = asToken(data.token);
  this.data = data;
}

function tokenFunction(states, config) {
  return function(stream, state) {
    if (state.pending) {
      var pend = state.pending.shift();
      if (state.pending.length == 0) state.pending = null;
      stream.pos += pend.text.length;
      return pend.token;
    }

    if (state.local) {
      if (state.local.end && stream.match(state.local.end)) {
        var tok = state.local.endToken || null;
        state.local = state.localState = null;
        return tok;
      } else {
        var tok = state.local.mode.token(stream, state.localState), m;
        if (state.local.endScan && (m = state.local.endScan.exec(stream.current())))
          stream.pos = stream.start + m.index;
        return tok;
      }
    }

    var curState = states[state.state];
    for (var i = 0; i < curState.length; i++) {
      var rule = curState[i];
      var matches = (!rule.data.sol || stream.sol()) && stream.match(rule.regex);
      if (matches) {
        if (rule.data.next) {
          state.state = rule.data.next;
        } else if (rule.data.push) {
          (state.stack || (state.stack = [])).push(state.state);
          state.state = rule.data.push;
        } else if (rule.data.pop && state.stack && state.stack.length) {
          state.state = state.stack.pop();
        }

        if (rule.data.mode)
          enterLocalMode(config, state, rule.data.mode, rule.token);
        if (rule.data.indent)
          state.indent.push(stream.indentation() + config.indentUnit);
        if (rule.data.dedent)
          state.indent.pop();
        var token = rule.token
        if (token && token.apply) token = token(matches)
        if (matches.length > 2 && rule.token && typeof rule.token != "string") {
          state.pending = [];
          for (var j = 2; j < matches.length; j++)
            if (matches[j])
              state.pending.push({text: matches[j], token: rule.token[j - 1]});
          stream.backUp(matches[0].length - (matches[1] ? matches[1].length : 0));
          return token[0];
        } else if (token && token.join) {
          return token[0];
        } else {
          return token;
        }
      }
    }
    stream.next();
    return null;
  };
}

function cmp(a, b) {
  if (a === b) return true;
  if (!a || typeof a != "object" || !b || typeof b != "object") return false;
  var props = 0;
  for (var prop in a) if (a.hasOwnProperty(prop)) {
    if (!b.hasOwnProperty(prop) || !cmp(a[prop], b[prop])) return false;
    props++;
  }
  for (var prop in b) if (b.hasOwnProperty(prop)) props--;
  return props == 0;
}

function enterLocalMode(config, state, spec, token) {
  var pers;
  if (spec.persistent) for (var p = state.persistentStates; p && !pers; p = p.next)
    if (spec.spec ? cmp(spec.spec, p.spec) : spec.mode == p.mode) pers = p;
  var mode = pers ? pers.mode : spec.mode || CodeMirror.getMode(config, spec.spec);
  var lState = pers ? pers.state : CodeMirror.startState(mode);
  if (spec.persistent && !pers)
    state.persistentStates = {mode: mode, spec: spec.spec, state: lState, next: state.persistentStates};

  state.localState = lState;
  state.local = {mode: mode,
                 end: spec.end && toRegex(spec.end),
                 endScan: spec.end && spec.forceEnd !== false && toRegex(spec.end, false),
                 endToken: token && token.join ? token[token.length - 1] : token};
}

function indexOf(val, arr) {
  for (var i = 0; i < arr.length; i++) if (arr[i] === val) return true;
}

function indentFunction(states, meta) {
  return function(state, textAfter, line) {
    if (state.local && state.local.mode.indent)
      return state.local.mode.indent(state.localState, textAfter, line);
    if (state.indent == null || state.local || meta.dontIndentStates && indexOf(state.state, meta.dontIndentStates) > -1)
      return CodeMirror.Pass;

    var pos = state.indent.length - 1, rules = states[state.state];
    scan: for (;;) {
      for (var i = 0; i < rules.length; i++) {
        var rule = rules[i];
        if (rule.data.dedent && rule.data.dedentIfLineStart !== false) {
          var m = rule.regex.exec(textAfter);
          if (m && m[0]) {
            pos--;
            if (rule.next || rule.push) rules = states[rule.next || rule.push];
            textAfter = textAfter.slice(m[0].length);
            continue scan;
          }
        }
      }
      break;
    }
    return pos < 0 ? 0 : state.indent[pos];
  };
}

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
/*
  An implementation of syntax highlighting for robot framework 3.1.

  http://robotframework.org/robotframework/3.1/RobotFrameworkUserGuide.html

  When necessary, the source code is consulted and ultimately trusted:

  https://github.com/robotframework/robotframework
*/
// tslint:disable-next-line
/// <reference path="../typings/codemirror/codemirror.d.ts"/>
// tslint:disable-next-line
/** helper function for compactly representing a rule */
function r(regex, token, opt) {
    return __assign({ regex: regex, token: token }, opt);
}
/** Possible Robot Framework table names. Group count is important.  */
var TABLE_NAMES = {
    keywords: /(\|\s)?(\*+ *)(user keywords?|keywords?)( *\**)/i,
    settings: /(\|\s)?(\*+ *)(settings?)( *\**)/i,
    test_cases: /(\|\s)?(\*+ *)(tasks?|test cases?)( *\**)/i,
    variables: /(\|\s)?(\*+ *)(variables?)( *\**)/i
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
var RULE_VAR_START = r(VAR_START, 'variable-2', { push: 'variable' });
/** a rule for the end of the variable state */
var RULE_VAR_END = r(VAR_END, 'variable-2');
/** a rule for a number */
var RULE_NUM = r(VAR_NUM, 'number');
/** a rule for starting a single quote */
var RULE_SINGLE_STRING_START = r(/'/, 'string', { push: 'single_string' });
/** a rule for starting a double quote */
var RULE_DOUBLE_STRING_START = r(/"/, 'string', { push: 'double_string' });
/** a rule for capturing tags (and friends) in keyword/test/task definitions */
var RULE_TAGS = r(/([|\s]*\s*)(\[\s*)(tags)(\s*\])(\s*\|?)/i, ['bracket', 'meta', 'meta', 'meta', 'bracket'], { sol: true, push: 'tags' });
/** rule for special case of applying tags at the suite level */
var RULE_SUITE_TAGS = r(/(force tags|default tags)(  +)/i, ['meta', null], {
    push: 'tags',
    sol: true
});
/** rule for special case of applying tags at the suite level (with pipes) */
var RULE_SUITE_TAGS_PIPE = r(/(\| +)(force tags|default tags)( *\|?)/i, ['bracket', 'meta', 'bracket'], { sol: true, push: 'tags' });
/** rule for bracketed settings of keyword/test/task */
var RULE_SETTING_KEYWORD = r(/([|\s]*)(\[\s*)(setup|teardown|template)(\s*\])(\s*\|?)/i, ['bracket', 'meta', 'meta', 'meta', 'bracket'], { push: 'keyword_invocation', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword */
var RULE_SUITE_SETTING_KEYWORD = r(/(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)(\t|  +)/i, ['meta', null], { push: 'keyword_invocation', sol: true });
/** rule for bracketed settings of keyword/test/task that include a keyword (with pipes) */
var RULE_SUITE_SETTING_KEYWORD_PIPE = r(/(\| +)(suite setup|suite teardown|test setup|test teardown|test template|task setup|task teardown|task template)( +\|)/i, ['bracket', 'meta', 'bracket'], { push: 'keyword_invocation', sol: true });
var RULE_SETTING_LIBRARY = r(/(library)(\t|  +)/i, ['meta', null], {
    push: 'library',
    sol: true
});
var RULE_SETTING_LIBRARY_PIPE = r(/(\| +)(library)( +\|)/i, ['bracket', 'meta', 'bracket'], { push: 'library', sol: true });
/** rule to escape the final closing bracket of a var at the end of a line */
var RULE_LINE_ENDS_WITH_VAR = r(/\}(?=$)/, 'variable-2', { pop: true });
/** collects the states that we build */
var states = {};
/** base isn't a state. these are the "normal business" that any state might use */
var base = RULES_TABLE.concat([
    RULE_VAR_START,
    RULE_VAR_END,
    r(/\|/, 'bracket'),
    r(/#.*$/, 'comment'),
    r(/\\ +/, 'bracket'),
    r(/\\(?=$)/, 'bracket'),
    r(/([^\s=]*)(=)/, ['attribute', 'operator']),
    r(/^(?!http|https)([^\s:]*)(:)/, ['attribute', 'operator']),
    r(/_\*.*?\*_/, 'string.strong.em'),
    r(/\*.*?\*/, 'string.strong'),
    r(/\_.*?\_/, 'string.em'),
    // this is pretty extreme, but seems to work
    r(/[^\s\$]+/, 'string')
]);
/** the starting state (begining of a file) */
states.start = [
    r(/(%%python)( module )?(.*)?/, ['meta', 'keyword', 'variable'], {
        mode: { spec: 'ipython' },
        sol: true
    }),
    r(/(%%[^\s]*).*$/, 'meta', { sol: true })
].concat(base);
/** settings states */
states.settings = [
    RULE_SUITE_TAGS_PIPE,
    RULE_SUITE_TAGS,
    RULE_SUITE_SETTING_KEYWORD_PIPE,
    RULE_SUITE_SETTING_KEYWORD,
    RULE_SETTING_LIBRARY,
    RULE_SETTING_LIBRARY_PIPE,
    r(/(\|*\s*)(resource|variables|documentation|metadata|test timeout|task timeout)(\s*)/i, ['bracket', 'meta', null], { sol: true })
].concat(base);
states.library = [
    RULE_LINE_ENDS_WITH_VAR,
    r(/WITH NAME$/, 'atom', { pop: true }),
    r(/WITH NAME/, 'atom'),
    r(/[^\}\|\s]*$/, 'string', { pop: true })
].concat(base);
var RULE_ELLIPSIS = r(/(\s*)(\.\.\.)/, [null, 'bracket']);
/** rule for behavior-driven-development keywords */
var RULE_START_BDD = r(/(\|\s*\|\s*|\s\s+)?(given|when|then|and|but)/i, ['bracket', 'builtin.em'], {
    push: 'keyword_invocation',
    sol: true
});
/** rule for whitespace keywords */
var RULE_KEY_START = r(/(\t+|  +)(?!\.\.\.)/, null, {
    push: 'keyword_invocation',
    sol: true
});
/** rule for pipe keywords */
var RULE_KEY_START_PIPE = r(/(\|\s*\|)(\s+)/, ['bracket', null], {
    push: 'keyword_invocation',
    sol: true
});
/** rule for for old-style loops (slashes) */
var RULE_START_LOOP_OLD = r(/(\s\|*\s*)(:FOR)(\s\|*\s*)/, [null, 'atom', null], {
    push: 'loop_start_old',
    sol: true
});
/** rule for for new-style loops (slashes) */
var RULE_START_LOOP_NEW = r(/(\s\|*\s*)(FOR)(\s\|*\s*)/, [null, 'atom', null], {
    push: 'loop_start_new',
    sol: true
});
/** rules for capturing individual tags */
states.tags = [
    r(/\s\|\s*/, 'bracket'),
    r(/^($|\n)/, null, { pop: true }),
    RULE_VAR_START,
    RULE_LINE_ENDS_WITH_VAR,
    RULE_VAR_END,
    r(/^\s*(?=$)/, null, { pop: true }),
    r(/ +/, null),
    r(/[^\$&%@]*?(?=(  +| \|))/, 'tag'),
    r(/[^\$&%@]*?(?=\s*\|?$)/, 'tag', { pop: true }),
    // fall back to single char
    r(/[^\$&%@|]/, 'tag')
];
/** need to catch empty white lines pretty explicitly */
var RULE_WS_LINE = r(/\s*(?=$)/, null, { sol: true });
/** not a state. rules for starting keyword invocation */
var RULES_KEYWORD_INVOKING = [
    RULE_START_BDD,
    RULE_KEY_START_PIPE,
    RULE_KEY_START,
    r(/\|\s(?=[^\s]*\|)/, null, { sol: true, push: 'keyword_invocation' }),
    r(/(?=[^\s])/, null, { sol: true, push: 'keyword_invocation' })
];
/** rules for data rows inside a keyword table */
states.keywords = [
    RULE_ELLIPSIS,
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    r(/([\|\s]*\s*)(\[\s*)(arguments|documentation|return|timeout)(\s*\])(\s*\|?)/i, ['bracket', 'meta', 'meta', 'meta', 'bracket'], { sol: true }),
    r(/(?=[^\s$&%@*|]+)/, null, { sol: true, push: 'keyword_def' }),
    RULE_START_LOOP_OLD,
    RULE_START_LOOP_NEW,
    RULE_WS_LINE
].concat(RULES_KEYWORD_INVOKING, base);
/** a keyword name fragment before an inline variable */
var KEYWORD_WORD_BEFORE_VAR = /([^\s]*?(?=[\$&%@]\{))/i;
/** a keyword name fragment before a separator */
var KEYWORD_WORD_BEFORE_SEP = /[^\s\|]+(?=$|[|]|\t)/;
/** a keyword name fragment before a non-separator whitespace character */
var KEYWORD_WORD_BEFORE_WS = /([^\n\$\s*=\|]+?(?= ))/i;
states.keyword_def = [
    RULE_VAR_START,
    r(/\}(?=$)/, 'variable-2'),
    RULE_VAR_END,
    r(/ /, null),
    r(KEYWORD_WORD_BEFORE_VAR, 'def'),
    r(KEYWORD_WORD_BEFORE_SEP, 'def', { pop: true }),
    r(KEYWORD_WORD_BEFORE_WS, 'def'),
    r(/(?=$)/, null, { sol: true, pop: true })
];
/** A range as used in for loops */
var RULE_RANGE = r(/([\|\s]*\s*)(IN)( RANGE| ENUMERATE| ZIP)?/, [
    null,
    'atom',
    'atom'
]);
states.loop_start_new = [
    RULE_RANGE,
    r(/[.]{3}/, 'bracket'),
    RULE_VAR_START,
    r(/\}(?=$)/, 'variable-2'),
    RULE_VAR_END,
    r(/([\|\s]*\s*)(END)/, [null, 'atom'], { sol: true, pop: true }),
    RULE_WS_LINE
].concat(RULES_KEYWORD_INVOKING, base);
states.loop_start_old = [
    r(/(?=.*)/, null, { sol: true, next: 'loop_body_old' }),
    RULE_RANGE,
    RULE_VAR_START,
    r(/\}(?=$)/, 'variable-2'),
    RULE_VAR_END
].concat(base);
states.loop_body_old = RULES_KEYWORD_INVOKING.map(function (rule) {
    return __assign({}, rule, { regex: new RegExp(/([\|\s]*\s*)(\\)/.source +
            (rule.regex instanceof RegExp ? rule.regex.source : rule.regex)), token: rule.token instanceof Array
            ? [null, 'bracket'].concat(rule.token) : [null, 'bracket', rule.token] });
}).concat([
    r(/(?=\s+[^\\])/, null, { pop: true, sol: true })
], base);
/** rules for data rows inside test/task definition */
states.test_cases = [
    RULE_ELLIPSIS,
    RULE_TAGS,
    RULE_SETTING_KEYWORD,
    r(/([\|\s]*\s*)(\[\s*)(documentation|timeout)(\s*\])/i, ['bracket', 'meta', 'meta', 'meta'], { sol: true }),
    RULE_START_LOOP_OLD,
    RULE_START_LOOP_NEW,
    r(/(\|\s+)([^\s*\|\.][^\|]*?)(\s*)(\|?$)/, ['bracket', 'string.header', 'bracket'], {
        sol: true
    }),
    r(/(\| +)(.+?)( \| )/, ['bracket', 'string.header', 'bracket'], {
        sol: true
    }),
    r(/([^|\s*].+$)/, 'string.header', { sol: true }),
    RULE_WS_LINE
].concat(RULES_KEYWORD_INVOKING, base);
/** rules for inside of an invoked keyword instance */
states.keyword_invocation = [
    r(/(?=\s*$)/, null, { pop: true }),
    r(/(\\|\.\.\.) +/, 'bracket', { pop: true }),
    RULE_VAR_START,
    RULE_LINE_ENDS_WITH_VAR,
    RULE_VAR_END,
    r(/#.*$/, 'comment', { pop: true }),
    r(/( \| |  +)/, 'bracket', { pop: true }),
    r(/ ?=(  +)/, 'operator'),
    r(/ /, null),
    r(KEYWORD_WORD_BEFORE_VAR, 'keyword'),
    r(KEYWORD_WORD_BEFORE_SEP, 'keyword', { pop: true }),
    r(KEYWORD_WORD_BEFORE_WS, 'keyword')
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
    r(/\}(?=\[)/, 'variable-2'),
    r(/[^}\n$]/, 'variable-2'),
    r(/^(?=\})/, 'variable-2', { pop: true })
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
    r(/([a-z_][a-z_\d]*)(=)/i, ['variable-2', 'operator']),
    r(/,/, 'punctuation'),
    r(/[^}](?=\})/, 'property', { pop: true }),
    r(/(^\})(\s*(?=$|\n))/, ['bracket', null], { pop: true }),
    r(/^\t*(?=$|\n)/, null, { pop: true }),
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
    r(/(\])(\})( ?=?)/, ['bracket', 'variable-2', 'operator'], { pop: true }),
    r(/(\])(\[)/, 'bracket'),
    r(/\]/, 'bracket', { pop: true }),
    r(/[^\]]/, 'string')
];

CodeMirror.defineSimpleMode(
    'robotframework',
    __assign({
        meta: {
            dontIndentStates: ['comment'],
            lineComment: '#'
        }
    }, states)
);
CodeMirror.defineMIME(
    'text/x-robotframework',
    'robotframework'
);
CodeMirror.modeInfo.push({
    ext: ['robot', 'resource'],
    mime: 'text/x-robotframework',
    mode: 'robotframework',
    name: 'robotframework'
});

})();
